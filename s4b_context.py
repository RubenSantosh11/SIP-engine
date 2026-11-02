"""Stage 4b: context fields for the brief's remaining questions, one record per LLM call.

  - what investors check, and how often            (checks)
  - what confuses or worries them inside the app   (worries)
  - what they do outside the app when unsure       (outside_help)
  - segment signals: age, income stability, source of money, who influenced them (segment)

Records with no cue word for any of these (config-free regex below) get empty values without an LLM call;
this saves calls but can miss signals phrased without a cue (documented in the Evidence Log).
Every value carries a verbatim span checked in code; values whose span fails are dropped and counted.
Writes data/processed/context.jsonl and outputs/context_summary.csv.
"""
import csv
import json
import re
from collections import Counter

from pydantic import ValidationError

import config
from sip.common import log, read_jsonl, write_jsonl
from sip.llm import BudgetExhausted, LLMError, PendingAnswer, cache_get, cache_put, llm_call
from sip.schema import ContextExtraction
from sip.spans import span_in_text

VERSION = "context-v1"
CUES = re.compile("|".join([
    r"check|xirr|nav\b|return|profit|loss|portfolio|track|statement|value|dekh",
    r"confus|worr|scared|fear|dar\b|doubt|don.?t know|not sure|samajh|understand|pata nahi|kya hoga|tension|panic|confidence",
    r"video|youtube|youtuber|friend|family|advisor|adviser|agent|google|influencer|podcast|channel|ca\b|bank rep|relationship manager|colleague|uncle|brother|varsity|interview",
    r"\bage\b|\d\d ?(yr|years? old|saal)|student|salary|income|job|emi|loan|saving|bonus|retire|housewife|freelanc|business|parents|wife|husband|son|daughter|kid|first salary|middle.?class|earning",
]), re.I)

SYSTEM = ("You fill a typed JSON schema for ONE piece of public feedback about SIPs. You never recommend funds or stocks. "
          "Evidence spans must be copied character-for-character from the text. Output JSON only.")
PROMPT = """Extract only what the TEXT states about the writer (or, for forum posts describing others, those investors). Leave lists empty and values "unclear" when not stated.

Return:
{{"record_id": "{record_id}",
 "checks": [{{"what": "returns_or_value"|"nav_or_units"|"instalment_status"|"portfolio_overall"|"other", "frequency": "daily"|"weekly"|"monthly"|"rarely"|"unclear", "evidence_span": "..."}}],
 "worries": [{{"kind": "losing_money"|"where_is_my_money"|"how_sip_works"|"charges_or_tax"|"app_status_or_error"|"whether_to_continue"|"other", "evidence_span": "..."}}],
 "outside_help": [{{"channel": "youtube_creator"|"friends_family"|"advisor_agent_bank"|"search_web"|"social_or_forum"|"customer_support"|"other", "evidence_span": "..."}}],
 "segment": {{"age_band": {{"value": "<25"|"25-34"|"35-44"|"45+"|"unclear", "evidence_span": ...}},
             "income_stability": {{"value": "salaried"|"irregular_or_business"|"student_no_income"|"retired"|"homemaker"|"unclear", "evidence_span": ...}},
             "money_source": {{"value": "salary_savings"|"lumpsum_or_windfall"|"family_money"|"unclear", "evidence_span": ...}},
             "influencer": {{"value": "self"|"youtube_creator"|"friends_family"|"advisor_agent_bank"|"ads_or_app"|"unclear", "evidence_span": ...}}}}}}
Rules: checks = what they look at after starting (returns, NAV, whether the instalment went through). worries = confusion or worry about the product or their SIP. outside_help = where they go or who they ask outside the app (a comment on a YouTube video counts as youtube_creator only if they say they rely on such content). Every evidence_span is an exact substring of the text (shorten, never reword or translate); null only when the value is unclear.

CONTEXT (video/topic title, background only): {context}
TEXT:
<<<
{text}
>>>"""


def spans_of(c: ContextExtraction):
    for group in ("checks", "worries", "outside_help"):
        for item in getattr(c, group):
            yield group, item.evidence_span
    for k, sig in c.segment.model_dump().items():
        if sig["value"] != "unclear":
            yield f"segment.{k}", sig["evidence_span"]


def clean(c: ContextExtraction, text: str) -> tuple[dict, int, int]:
    """Drop any value whose span is not in the text; return (dict, n_values, n_dropped)."""
    d = c.model_dump()
    n = dropped = 0
    for group in ("checks", "worries", "outside_help"):
        keep = []
        for item in d[group]:
            n += 1
            if span_in_text(item["evidence_span"], text):
                keep.append(item)
            else:
                dropped += 1
        d[group] = keep
    for k, sig in d["segment"].items():
        if sig["value"] != "unclear":
            n += 1
            if not span_in_text(sig["evidence_span"], text):
                dropped += 1
                d["segment"][k] = {"value": "unclear", "evidence_span": None}
    return d, n, dropped


def main() -> None:
    records = read_jsonl(config.PROCESSED_DIR / "relevant.jsonl")
    pending = 0
    for r in records:
        if cache_get("context", r["record_id"], VERSION) is not None:
            continue
        if not CUES.search(r["text"]):
            cache_put("context", r["record_id"], VERSION, {**ContextExtraction(record_id=r["record_id"]).model_dump(),
                                                            "routed": "no_cue", "n_values": 0, "n_dropped": 0})
            continue
        try:
            out = llm_call(config.MODEL_EXTRACT, PROMPT.format(record_id=r["record_id"], context=r.get("context") or "-",
                                                               text=r["text"][:4000]), SYSTEM,
                           key=f"context__{VERSION}__{r['record_id']}")
            c = ContextExtraction.model_validate(out)
            d, n, dropped = clean(c, r["text"])
            cache_put("context", r["record_id"], VERSION, {**d, "routed": "llm", "n_values": n, "n_dropped": dropped})
        except PendingAnswer:
            pending += 1
        except (LLMError, ValidationError) as e:
            log.warning("%s: %s", r["record_id"], str(e)[:200])
        except BudgetExhausted as e:
            log.warning("stopping cleanly: %s", e)
            break
    if pending:
        log.info("%d context requests queued", pending)
        return
    rows = [cache_get("context", r["record_id"], VERSION) for r in records]
    write_jsonl(config.PROCESSED_DIR / "context.jsonl", rows)

    # Aggregate in Python: counts per category, overall and by dropper / continuer status
    ex = {x["record_id"]: x for x in read_jsonl(config.PROCESSED_DIR / "extractions.jsonl")}
    group = lambda rid: ("dropper" if ex[rid]["sip_status"] in config.DROPPER_STATUSES
                         else "continuer" if ex[rid]["sip_status"] in config.CONTINUER_STATUSES else "unclear")
    counts = Counter()
    for c in rows:
        g = group(c["record_id"])
        seen = set()
        for item in c["checks"]:
            seen.add(("check", item["what"])); seen.add(("check_frequency", item["frequency"]))
        for item in c["worries"]:
            seen.add(("worry", item["kind"]))
        for item in c["outside_help"]:
            seen.add(("outside_help", item["channel"]))
        for k, sig in c["segment"].items():
            if sig["value"] != "unclear":
                seen.add((f"segment_{k}", sig["value"]))
        for key in seen:  # count records, not mentions
            counts[(*key, "all")] += 1
            counts[(*key, g)] += 1
    with open(config.OUTPUT_DIR / "context_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["field", "value", "records_all", "records_dropper", "records_continuer", "records_unclear_status"])
        for field, value in sorted({(a, b) for a, b, _ in counts}):
            w.writerow([field, value, counts[(field, value, "all")], counts[(field, value, "dropper")],
                        counts[(field, value, "continuer")], counts[(field, value, "unclear")]])
    n = sum(c["n_values"] for c in rows)
    dropped = sum(c["n_dropped"] for c in rows)
    stats = {"records": len(rows), "routed_to_llm": sum(c["routed"] == "llm" for c in rows),
             "values_coded": n, "values_dropped_span_fail": dropped}
    (config.OUTPUT_DIR / "context_stats.json").write_text(json.dumps(stats, indent=1))
    log.info("%s", stats)


if __name__ == "__main__":
    main()
