"""Stage 2: relevance filter (research questions: start / behaviour after starting / pause-reduce-stop).

1. Keyword pre-filter (free): the text must mention SIPs / auto-invest / monthly investing, OR the
   context (video or topic title) mentions SIPs and the text uses a stop/pause/continue-type word.
2. Batched LLM filter (10 records per call) on the survivors.
Results are cached per record (record_id + prompt version), so re-runs never repeat finished work.
Writes data/processed/relevant.jsonl and outputs/filter_stats.json.
"""
import json
import re
from collections import Counter

from pydantic import TypeAdapter, ValidationError

import config
from sip.common import log, read_jsonl, sha, write_jsonl
from sip.llm import BudgetExhausted, LLMError, PendingAnswer, cache_get, cache_put, llm_call
from sip.schema import FilterItem

SOURCES = ["playstore", "appstore", "youtube", "tradingqna"]
SIP_RE = re.compile("|".join(config.SIP_TERMS), re.I)
ACTION_RE = re.compile("|".join(config.ACTION_TERMS), re.I)

SYSTEM = "You are a careful research assistant classifying public feedback. Output JSON only."
PROMPT = """Decide for each numbered item whether it is RELEVANT to a study of SIPs (systematic investment plans in mutual funds, incl. auto-invest / monthly mutual-fund investing) with three questions:
  (A) Why do people start a SIP, and what do they expect to happen?
  (B) What changes in their behaviour in the months after starting (checking returns, increasing, reducing, skipping, redeeming, switching, sticking with it)?
  (C) What leads investors to pause, reduce or stop a SIP?

RELEVANT = the text describes the writer's own (or other investors') SIP experience, motives, expectations, behaviour or decisions that speak to A, B or C - including payment/mandate/app problems that make a SIP miss or stop.
NOT RELEVANT = generic praise or complaints about the app, stock trading only, SIPs merely named with nothing about motives/expectations/behaviour/decisions, spam or promotion, thanks to a video creator, or bare how-to questions with no personal situation.
The context line (video or forum topic title) is background only; judge the text.

Return a JSON array with one object per item: [{{"i": <item number>, "relevant": true|false}}]

ITEMS:
{items}"""


def prefilter(r: dict) -> bool:
    if SIP_RE.search(r["text"]):
        return True
    return bool(r.get("context") and SIP_RE.search(r["context"]) and ACTION_RE.search(r["text"]))


def run_batch(batch: list[dict]) -> None:
    items = "\n\n".join(
        f"[{i}] (source: {r['source']}; context: {r.get('context') or '-'})\n{r['text'][:1500]}"
        for i, r in enumerate(batch, 1))
    key = f"filter__{config.PROMPT_VERSION_FILTER}__{sha(','.join(r['record_id'] for r in batch), 16)}"
    out = llm_call(config.MODEL_FILTER, PROMPT.format(items=items), SYSTEM, key=key)
    parsed = TypeAdapter(list[FilterItem]).validate_python(out)
    by_i = {p.i: p.relevant for p in parsed}
    if set(by_i) != set(range(1, len(batch) + 1)):
        raise LLMError(f"filter batch {key}: item numbers do not match")
    model = config.SESSION_MODEL_LABEL if config.LLM_PROVIDER == "session" else config.MODEL_FILTER
    for i, r in enumerate(batch, 1):
        cache_put("filter", r["record_id"], config.PROMPT_VERSION_FILTER, {"relevant": by_i[i], "model": model})


def main() -> None:
    records = [r for s in SOURCES for r in read_jsonl(config.RAW_DIR / f"{s}.jsonl")]
    candidates = [r for r in records if prefilter(r)]
    todo = [r for r in candidates if cache_get("filter", r["record_id"], config.PROMPT_VERSION_FILTER) is None]
    n_batches = -(-len(todo) // config.FILTER_BATCH_SIZE)
    log.info("%d raw, %d pass keyword pre-filter, %d need LLM -> %d batched requests",
             len(records), len(candidates), len(todo), n_batches)

    pending = failed = 0
    for start in range(0, len(todo), config.FILTER_BATCH_SIZE):
        batch = todo[start:start + config.FILTER_BATCH_SIZE]
        try:
            run_batch(batch)
        except PendingAnswer:
            pending += 1
        except (LLMError, ValidationError) as e:
            failed += 1
            log.warning("batch failed: %s", str(e)[:200])
        except BudgetExhausted as e:
            log.warning("stopping cleanly: %s", e)
            break

    stats = {s: Counter() for s in SOURCES}
    relevant = []
    for r in records:
        st = stats[r["source"]]
        st["raw"] += 1
        if not prefilter(r):
            st["dropped_prefilter"] += 1
            continue
        st["pass_prefilter"] += 1
        c = cache_get("filter", r["record_id"], config.PROMPT_VERSION_FILTER)
        if c is None:
            st["pending_llm"] += 1
        elif c["relevant"]:
            st["kept"] += 1
            relevant.append(r)
        else:
            st["dropped_llm"] += 1
    write_jsonl(config.PROCESSED_DIR / "relevant.jsonl", relevant)
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    (config.OUTPUT_DIR / "filter_stats.json").write_text(json.dumps({s: dict(c) for s, c in stats.items()}, indent=1))
    for s, c in stats.items():
        log.info("%-10s %s", s, dict(c))
    if pending:
        log.info("%d batches queued for the session model in %s", pending, config.SESSION_DIR / "requests")
    if failed:
        log.info("%d batches failed validation; re-run to retry", failed)


if __name__ == "__main__":
    main()
