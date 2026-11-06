"""Stage 4: structured extraction, one record per LLM call, against the codebook.

Every coded value must quote the source verbatim. Spans are checked in code (whitespace + case
normalisation only). If any span fails: retry once; values that still fail are kept but marked
verified=false and excluded from counts. Malformed output (pydantic) also gets one retry.
Writes data/processed/extractions.jsonl and outputs/span_check_stats.json.
"""
import json

import yaml
from pydantic import ValidationError

import config
from sip.common import log, read_jsonl, write_jsonl
from sip.llm import BudgetExhausted, LLMError, PendingAnswer, cache_get, cache_put, llm_call
from sip.schema import Extraction
from sip.spans import span_in_text

SYSTEM = ("You fill a typed JSON schema for ONE piece of public feedback. You never recommend funds or stocks. "
          "Evidence spans must be copied character-for-character from the text. Output JSON only.")

PROMPT = """Code this {source} text about SIPs (systematic investment plans in mutual funds).

CODEBOOK (use only these theme_id values, or "other"):
{codebook}

Return one JSON object:
{{
 "record_id": "{record_id}",
 "source": "{source}",
 "sip_status": "stopped" | "paused" | "reduced" | "continuing" | "unclear",   // the WRITER's own SIP status as stated
 "sip_status_evidence": "<verbatim quote showing the status, or null if unclear>",
 "first_time_investor": "yes" | "no" | "unclear",                // only "yes"/"no" if the text says so
 "first_time_evidence": "<verbatim quote, or null if unclear>",
 "time_since_start": "<1m" | "1-6m" | "6-12m" | ">12m" | "unclear",   // how long the writer has had the SIP, if stated
 "time_since_start_evidence": "<verbatim quote, or null if unclear>",
 "themes": [{{"theme_id": "...", "evidence_span": "<verbatim quote>", "severity": 1|2|3, "confidence": 0.0-1.0}}],
 "one_line_reason": "<why they stopped/paused/continued, max 20 words, or null>"
}}
Rules:
- stopped = cancelled/ended (or clearly says "I want to stop my SIP"); paused = paused/skipped/missed instalments but keeping it; reduced = lowered the amount; continuing = still investing. A question like "should I stop?" is unclear.
- Themes answer three questions: why they started and what they expected (start), how their behaviour changed after starting (behaviour), what led them to pause/reduce/stop (stop). Code only themes the text actually supports.
- severity: 1 = minor mention, 2 = clear reason or friction, 3 = decisive reason / strong distress.
- Every evidence quote must be an exact substring of the text (you may shorten it, never reword or translate it).
{retry_note}
CONTEXT (video/topic title, background only): {context}
TEXT:
<<<
{text}
>>>"""


def load_codebook() -> dict:
    return yaml.safe_load(config.CODEBOOK_PATH.read_text())


def codebook_text(cb: dict) -> str:
    return "\n".join(f"- {t['id']} [{t.get('question', '?')}]: {t['name']}. {t['definition']} "
                     f"Include: {t['include']} Exclude: {t['exclude']}" for t in cb["themes"])


def failed_spans(ex: Extraction, text: str) -> list[str]:
    bad = [t.evidence_span for t in ex.themes if not span_in_text(t.evidence_span, text)]
    if ex.sip_status != "unclear" and not span_in_text(ex.sip_status_evidence, text):
        bad.append(ex.sip_status_evidence or "<missing sip_status_evidence>")
    if ex.first_time_investor != "unclear" and not span_in_text(ex.first_time_evidence, text):
        bad.append(ex.first_time_evidence or "<missing first_time_evidence>")
    if ex.time_since_start != "unclear" and not span_in_text(ex.time_since_start_evidence, text):
        bad.append(ex.time_since_start_evidence or "<missing time_since_start_evidence>")
    return bad


def call(r: dict, cb: dict, attempt: int, note: str) -> Extraction:
    prompt = PROMPT.format(source=r["source"], record_id=r["record_id"], codebook=codebook_text(cb),
                           context=r.get("context") or "-", text=r["text"][:4000], retry_note=note)
    key = f"extract__{config.PROMPT_VERSION_EXTRACT}__{r['record_id']}__a{attempt}"
    out = llm_call(config.MODEL_EXTRACT, prompt, SYSTEM, key=key)
    return Extraction.model_validate(out, context={"theme_ids": {t["id"] for t in cb["themes"]}})


def extract(r: dict, cb: dict) -> dict:
    """Up to two attempts. Returns the final cached dict with verification flags."""
    note, attempts, ex, err = "", 0, None, None
    for attempt in range(2):
        attempts = attempt + 1
        try:
            ex = call(r, cb, attempt, note)
        except ValidationError as e:
            err = f"malformed: {e.errors()[0]['msg']}"
            note = f"\nYOUR PREVIOUS ANSWER WAS REJECTED ({err}). Follow the schema exactly.\n"
            ex = None
            continue
        bad = failed_spans(ex, r["text"])
        if not bad:
            break
        note = ("\nYOUR PREVIOUS ANSWER WAS REJECTED: these quotes are not exact substrings of the text: "
                + json.dumps(bad, ensure_ascii=False) + ". Copy quotes exactly.\n")
    if ex is None:
        return {"record_id": r["record_id"], "source": r["source"], "status": "malformed", "error": err, "attempts": attempts}

    d = ex.model_dump()
    d["status"] = "ok"
    d["attempts"] = attempts
    for t in d["themes"]:
        t["verified"] = span_in_text(t["evidence_span"], r["text"])
    d["sip_status_verified"] = d["sip_status"] == "unclear" or span_in_text(d["sip_status_evidence"], r["text"])
    d["first_time_verified"] = d["first_time_investor"] == "unclear" or span_in_text(d["first_time_evidence"], r["text"])
    d["time_since_start_verified"] = (d["time_since_start"] == "unclear"
                                      or span_in_text(d["time_since_start_evidence"], r["text"]))
    d["model"] = config.SESSION_MODEL_LABEL if config.LLM_PROVIDER == "session" else config.MODEL_EXTRACT
    d["codebook_status"] = cb.get("status")
    return d


def main() -> None:
    cb = load_codebook()
    if cb.get("status") != "final":
        log.warning("codebook status is %r (not final): results are for plumbing tests only", cb.get("status"))
    records = read_jsonl(config.PROCESSED_DIR / "relevant.jsonl")
    todo = [r for r in records if cache_get("extract", r["record_id"], config.PROMPT_VERSION_EXTRACT) is None]
    log.info("%d relevant records, %d still to extract (about %d-%d requests incl. retries)",
             len(records), len(todo), len(todo), 2 * len(todo))
    pending = 0
    for r in todo:
        try:
            cache_put("extract", r["record_id"], config.PROMPT_VERSION_EXTRACT, extract(r, cb))
        except PendingAnswer:
            pending += 1
        except LLMError as e:
            log.warning("%s: %s", r["record_id"], str(e)[:200])
        except BudgetExhausted as e:
            log.warning("stopping cleanly: %s", e)
            break

    rows = [c for r in records if (c := cache_get("extract", r["record_id"], config.PROMPT_VERSION_EXTRACT))]
    write_jsonl(config.PROCESSED_DIR / "extractions.jsonl", rows)

    ok = [x for x in rows if x["status"] == "ok"]
    spans = [t["verified"] for x in ok for t in x["themes"]]
    spans += [x["sip_status_verified"] for x in ok if x["sip_status"] != "unclear"]
    spans += [x["first_time_verified"] for x in ok if x["first_time_investor"] != "unclear"]
    spans += [x["time_since_start_verified"] for x in ok if x.get("time_since_start", "unclear") != "unclear"]
    stats = {
        "records_extracted": len(rows),
        "malformed_after_retry": sum(x["status"] == "malformed" for x in rows),
        "needed_retry": sum(x.get("attempts", 1) > 1 for x in rows),
        "coded_values_with_span": len(spans),
        "span_failures_after_retry": spans.count(False),
        "span_pass_rate": round(spans.count(True) / len(spans), 4) if spans else None,
        "pending": pending,
    }
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    (config.OUTPUT_DIR / "span_check_stats.json").write_text(json.dumps(stats, indent=1))
    log.info("span check: %s", stats)
    if pending:
        log.info("%d extraction requests queued in %s", pending, config.SESSION_DIR / "requests")


if __name__ == "__main__":
    main()
