"""Stage 3: open coding of a stratified sample, then clustering into a DRAFT codebook.

1. Sample ~100 relevant records, spread as evenly as possible across sources (fixed seed).
2. One LLM call per record: free-text codes under the three research questions, each with a verbatim quote.
   Quotes are span-checked; codes whose quote fails are dropped (and counted).
3. One LLM call clusters the code labels into candidate themes. Member counts and example quotes are
   filled in by Python, not the LLM.
Writes outputs/open_codes.jsonl and codebook_draft.yaml. You then curate codebook.yaml by hand.
"""
import json
import random
from collections import defaultdict

import yaml
from pydantic import BaseModel, ValidationError

import config
from sip.common import log, read_jsonl, write_jsonl
from sip.llm import BudgetExhausted, LLMError, PendingAnswer, cache_get, cache_put, llm_call
from sip.schema import OpenCode
from sip.spans import span_in_text

SAMPLE_SIZE = 100
SEED = 42

SYSTEM = ("You are a qualitative researcher doing open coding of public feedback about SIPs. "
          "You never recommend funds or stocks. Quotes must be copied character-for-character. Output JSON only.")

PROMPT = """Open-code this {source} text. Research questions:
  start     - Why did the person start a SIP, and what did they expect to happen?
  behaviour - What changed in their behaviour in the months after starting (checking returns, increasing,
              reducing, skipping, redeeming, switching, sticking with it, feelings about it)?
  stop      - What led them (or investors they describe) to pause, reduce or stop a SIP, or nearly do so?

Write short free-text codes (2-8 words, your own words) for every distinct idea the text supports. Several
codes per question are fine; skip questions the text says nothing about. Each code needs a verbatim quote
(an exact substring of the text; shorten it but never reword or translate).

Return: {{"record_id": "{record_id}", "codes": [{{"question": "start"|"behaviour"|"stop", "code": "...", "quote": "..."}}]}}

CONTEXT (video/topic title, background only): {context}
TEXT:
<<<
{text}
>>>"""

CLUSTER_PROMPT = """Below are open codes from {n_records} public comments about SIPs, grouped by research question.
Cluster them into candidate THEMES for a codebook (aim for 5-9 themes per question; merge near-duplicates;
put rare one-offs into an "other_<question>" theme).

For each theme return: id (snake_case), question (start|behaviour|stop), name, definition (one sentence),
include (what counts), exclude (what does not, and which other theme to use instead),
addressability (high = Groww can change it in product/copy/flows; medium = Groww can influence it via
education, reminders or defaults; low = mostly outside Groww's control), exclude_from_droppers (true only for
"stops" that are really switches of plan/platform, not leaving SIP investing), and members (the code numbers).
Every code number must appear in exactly one theme. No fund or stock recommendations, and no fear/FOMO/urgency wording.

Return a JSON array: [{{"id": "...", "question": "...", "name": "...", "definition": "...", "include": "...",
"exclude": "...", "addressability": "high"|"medium"|"low", "members": [<code numbers>]}}]

CODES:
{codes}"""


class DraftTheme(BaseModel):
    id: str
    question: str
    name: str
    definition: str
    include: str
    exclude: str
    addressability: str
    exclude_from_droppers: bool = False
    members: list[int]


def stratified_sample(records: list[dict], n: int) -> list[dict]:
    by_src = defaultdict(list)
    for r in records:
        by_src[r["source"]].append(r)
    rng = random.Random(SEED)
    for rows in by_src.values():
        rng.shuffle(rows)
    picked, quota = [], {s: 0 for s in by_src}
    while len(picked) < n and any(quota[s] < len(by_src[s]) for s in by_src):
        for s in sorted(by_src):  # round-robin = as even as availability allows
            if quota[s] < len(by_src[s]) and len(picked) < n:
                picked.append(by_src[s][quota[s]])
                quota[s] += 1
    log.info("sample: %s", quota)
    return picked


def open_code(r: dict) -> dict:
    key = f"opencode__{config.PROMPT_VERSION_OPENCODE}__{r['record_id']}"
    out = llm_call(config.MODEL_EXTRACT, PROMPT.format(source=r["source"], record_id=r["record_id"],
                   context=r.get("context") or "-", text=r["text"][:4000]), SYSTEM, key=key)
    oc = OpenCode.model_validate(out)
    codes = [c.model_dump() | {"verified": span_in_text(c.quote, r["text"])} for c in oc.codes]
    return {"record_id": r["record_id"], "source": r["source"], "codes": codes}


def main() -> None:
    records = read_jsonl(config.PROCESSED_DIR / "relevant.jsonl")
    sample = stratified_sample(records, SAMPLE_SIZE)
    pending = 0
    for r in sample:
        if cache_get("opencode", r["record_id"], config.PROMPT_VERSION_OPENCODE) is not None:
            continue
        try:
            cache_put("opencode", r["record_id"], config.PROMPT_VERSION_OPENCODE, open_code(r))
        except PendingAnswer:
            pending += 1
        except (LLMError, ValidationError) as e:
            log.warning("%s: %s", r["record_id"], str(e)[:200])
        except BudgetExhausted as e:
            log.warning("stopping cleanly: %s", e)
            return
    if pending:
        log.info("%d open-coding requests queued in %s; answer them and re-run", pending, config.SESSION_DIR / "requests")
        return

    coded = [c for r in sample if (c := cache_get("opencode", r["record_id"], config.PROMPT_VERSION_OPENCODE))]
    write_jsonl(config.OUTPUT_DIR / "open_codes.jsonl", coded)
    flat = [(x["record_id"], x["source"], c) for x in coded for c in x["codes"] if c["verified"]]
    n_all = sum(len(x["codes"]) for x in coded)
    log.info("%d records coded, %d codes, %d with verified quotes (%d dropped)", len(coded), n_all, len(flat), n_all - len(flat))

    codes_txt = "\n".join(f"{i} [{c['question']}] {c['code']}" for i, (_, _, c) in enumerate(flat))
    key = f"cluster__{config.PROMPT_VERSION_OPENCODE}__n{len(flat)}"
    try:
        out = llm_call(config.MODEL_EXTRACT, CLUSTER_PROMPT.format(n_records=len(coded), codes=codes_txt), SYSTEM, key=key)
    except PendingAnswer:
        log.info("clustering request queued: %s", key)
        return
    themes = [DraftTheme.model_validate(t) for t in out]

    seen = [m for t in themes for m in t.members]
    log.info("clustering covered %d/%d codes (%d duplicates)", len(set(seen)), len(flat), len(seen) - len(set(seen)))
    draft = []
    for t in themes:
        members = [flat[m] for m in t.members if 0 <= m < len(flat)]
        quotes = sorted(members, key=lambda x: -len(x[2]["quote"]))  # longest quote = most context
        draft.append({
            "id": t.id, "question": t.question, "name": t.name, "definition": t.definition,
            "include": t.include, "exclude": t.exclude,
            "example": quotes[0][2]["quote"] if quotes else "",
            "example_source": quotes[0][1] if quotes else "",
            "addressability": t.addressability,
            "exclude_from_droppers": t.exclude_from_droppers,
            "draft_n_codes": len(members),                               # counted in Python
            "draft_n_records": len({m[0] for m in members}),
            "draft_sources": sorted({m[1] for m in members}),
            "draft_member_codes": [m[2]["code"] for m in members][:12],
        })
    draft.sort(key=lambda d: (d["question"], -d["draft_n_records"]))
    header = ("# DRAFT codebook from Stage 3 open coding. Curate it into codebook.yaml (merge, rename, delete),\n"
              "# set status: final, and log your edits in corrections_log.md. draft_* fields are for your reference.\n")
    body = {"status": "draft", "addressability_scores": yaml.safe_load(config.CODEBOOK_PATH.read_text())["addressability_scores"],
            "themes": draft}
    (config.ROOT / "codebook_draft.yaml").write_text(header + yaml.safe_dump(body, sort_keys=False, allow_unicode=True, width=110))
    log.info("wrote codebook_draft.yaml with %d themes", len(draft))


if __name__ == "__main__":
    main()
