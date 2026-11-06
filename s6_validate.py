"""Stage 6: golden-set validation.

  python s6_validate.py blank   -> outputs/golden_set_blank.csv (20 records, engine output hidden, empty label columns)
  python s6_validate.py score   -> reads outputs/golden_set_labelled.csv, compares with the engine, writes
                                   outputs/validation_summary.json and outputs/validation_failures.csv

The sample is drawn from the relevant records BEFORE extraction (fixed seed), stratified across sources
and apps, so it cannot be steered by what the engine outputs.

Label columns (fill by hand, without looking at engine output):
  sip_status           stopped | paused | reduced | continuing | unclear
  first_time_investor  yes | no | unclear
  time_since_start     <1m | 1-6m | 6-12m | >12m | unclear
  themes               theme_id:severity pairs separated by ';'   e.g.  payment_autopay_failure:2; fees_paywall:3
                       (leave empty if no codebook theme applies)
"""
import csv
import json
import random
import sys
from collections import defaultdict

import yaml

import config
from sip.common import read_jsonl

N = 20
SEED = 7
QUOTA = {"playstore": 8, "appstore": 3, "youtube": 5, "tradingqna": 3, "valuepickr": 1}
LABELS = ["sip_status", "first_time_investor", "time_since_start", "themes", "notes"]


def blank() -> None:
    # Exclude records whose engine output the labeller has already seen (thin-slice review table).
    seen = {json.loads(l)["record_id"] for l in open(config.ROOT / "data" / "processed" / "thin_slice_ids.json")} \
        if (config.ROOT / "data" / "processed" / "thin_slice_ids.json").exists() else set()
    records = [r for r in read_jsonl(config.PROCESSED_DIR / "relevant.jsonl") if r["record_id"] not in seen]
    rng = random.Random(SEED)
    picked = []
    for src, k in QUOTA.items():
        by_app = defaultdict(list)
        for r in records:
            if r["source"] == src:
                by_app[r.get("app") or "-"].append(r)
        apps = sorted(by_app)
        for a in apps:
            rng.shuffle(by_app[a])
        i = 0
        while sum(p["source"] == src for p in picked) < k and any(by_app.values()):
            a = apps[i % len(apps)]
            if by_app[a]:
                picked.append(by_app[a].pop())
            i += 1
    path = config.OUTPUT_DIR / "golden_set_blank.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["golden_id", "record_id", "source", "app", "context", "text"] + LABELS)
        for i, r in enumerate(picked, 1):
            w.writerow([i, r["record_id"], r["source"], r.get("app") or "", r.get("context") or "", r["text"]] + [""] * len(LABELS))
    print(f"wrote {path} with {len(picked)} records")


def parse_themes(cell: str) -> dict:
    out = {}
    for part in (cell or "").replace(",", ";").split(";"):
        part = part.strip()
        if not part:
            continue
        tid, _, sev = part.partition(":")
        out[tid.strip()] = int(sev) if sev.strip().isdigit() else None
    return out


BOUNDARIES = [({"payment_autopay_failure", "app_reliability_errors"}, "codebook boundary: payment failure vs app processing error"),
              ({"early_confusion_first_months", "conflicting_advice", "return_expectations", "other"},
               "codebook boundary: early confusion vs advice / expectations"),
              ({"switching_plan_or_platform", "platform_or_fund_initiated"}, "codebook boundary: switching vs platform-initiated"),
              ({"support_trust_breakdown", "app_reliability_errors"}, "codebook boundary: support vs app error")]


def cause_of(f: dict) -> str:
    """Deterministic first-pass cause for a disagreement; the PM can overrule it in the failures table."""
    field, mine, eng = f["field"], str(f["my_label"]), str(f["engine_output"])
    if field == "sip_status":
        if mine not in {"stopped", "paused", "reduced", "continuing", "unclear"}:
            return "label outside the scheme"
        return "engine stricter: status implied, not stated" if eng == "unclear" else "different reading of status"
    if field == "first_time_investor":
        return "engine stricter: only codes what the text states" if eng == "unclear" else "different reading"
    if field == "time_since_start":
        return "engine missed or did not infer a stated period" if eng == "unclear" else "different period from the same text"
    if field.startswith("theme:"):
        return "engine over-coded or used a neighbouring theme" if eng == "True" else "engine missed it or used a neighbouring theme"
    return "severity judgement"


def score(engine_file: str = "extractions.jsonl", suffix: str = "") -> None:
    codebook = yaml.safe_load(config.CODEBOOK_PATH.read_text())
    theme_ids = [t["id"] for t in codebook["themes"]]
    labelled = list(csv.DictReader(open(config.OUTPUT_DIR / "golden_set_labelled.csv", encoding="utf-8")))
    engine = {r["record_id"]: r for r in read_jsonl(config.PROCESSED_DIR / engine_file)}
    agree = defaultdict(lambda: [0, 0])  # field -> [agreements, comparisons]
    failures = []

    def compare(field, mine, theirs, rid, cause=""):
        agree[field][1] += 1
        if mine == theirs:
            agree[field][0] += 1
        else:
            failures.append({"record_id": rid, "field": field, "my_label": mine, "engine_output": theirs, "likely_cause": cause})

    for row in labelled:
        rid = row["record_id"]
        e = engine.get(rid)
        if not e or e.get("status") != "ok":
            failures.append({"record_id": rid, "field": "all", "my_label": "-", "engine_output": "missing/malformed", "likely_cause": "extraction failed"})
            continue
        for f in ["sip_status", "first_time_investor", "time_since_start"]:
            if row.get(f, "").strip():
                compare(f, row[f].strip(), e.get(f, "unclear"), rid)
        mine = parse_themes(row.get("themes", ""))
        eng = {t["theme_id"]: t["severity"] for t in e["themes"] if t.get("verified")}
        for tid in theme_ids:
            compare(f"theme:{tid}", tid in mine, tid in eng, rid,
                    "engine missed it" if tid in mine else ("engine over-coded" if tid in eng else ""))
            if tid in mine and tid in eng and mine[tid] is not None:
                agree["severity_within_1"][1] += 1
                if abs(mine[tid] - eng[tid]) <= 1:
                    agree["severity_within_1"][0] += 1
                else:
                    failures.append({"record_id": rid, "field": f"severity:{tid}", "my_label": mine[tid],
                                     "engine_output": eng[tid], "likely_cause": "severity judgement"})

    # Theme precision / recall over positive labels (the per-theme table is dominated by true negatives)
    tp = fp = fn = overlap = 0
    for row in labelled:
        e = engine.get(row["record_id"])
        if not e or e.get("status") != "ok":
            continue
        mine = {t for t in parse_themes(row.get("themes", "")) if t in theme_ids or t == "other"}
        eng = {t["theme_id"] for t in e["themes"] if t.get("verified")}
        tp += len(mine & eng); fp += len(eng - mine); fn += len(mine - eng)
        overlap += bool(mine & eng) or (not mine and not eng)
    labels_by_id = {row["record_id"]: row for row in labelled}
    for f in failures:
        f["likely_cause"] = f["likely_cause"] or cause_of(f)
        if f["field"].startswith("theme:") and f["record_id"] in engine:
            mine = set(parse_themes(labels_by_id[f["record_id"]].get("themes", "")))
            eng = {t["theme_id"] for t in engine[f["record_id"]]["themes"] if t.get("verified")}
            for pair, label in BOUNDARIES:
                if (mine & pair) and (eng & pair) and (mine & pair) != (eng & pair):
                    f["likely_cause"] = label
                    break
    theme_fields = [k for k in agree if k.startswith("theme:")]
    any_theme = [sum(agree[k][0] for k in theme_fields), sum(agree[k][1] for k in theme_fields)]
    summary = {
        "n_labelled": len(labelled),
        "agreement": {k: {"agree": a, "n": n, "pct": round(100 * a / n, 1) if n else None}
                      for k, (a, n) in sorted(agree.items())},
        "theme_presence_overall_pct": round(100 * any_theme[0] / any_theme[1], 1) if any_theme[1] else None,
        "theme_precision": round(tp / (tp + fp), 3) if tp + fp else None,
        "theme_recall": round(tp / (tp + fn), 3) if tp + fn else None,
        "records_theme_overlap": overlap,
        "span_check": json.loads((config.OUTPUT_DIR / "span_check_stats.json").read_text()),
    }
    (config.OUTPUT_DIR / f"validation_summary{suffix}.json").write_text(json.dumps(summary, indent=1))
    with open(config.OUTPUT_DIR / f"validation_failures{suffix}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["record_id", "field", "my_label", "engine_output", "likely_cause"])
        w.writeheader()
        w.writerows(failures)
    print(json.dumps({k: v for k, v in summary.items() if k != "agreement"}, indent=1))
    for k, v in summary["agreement"].items():
        if not k.startswith("theme:") or v["pct"] != 100.0:
            print(f"{k:45} {v['agree']}/{v['n']} = {v['pct']}%")


def gemini() -> None:
    """Run the deployed model (Gemini) on the 20 golden records, then score it the same way."""
    import yaml
    from sip import llm
    import s4_extract
    config.LLM_PROVIDER = "gemini"
    cb = yaml.safe_load(config.CODEBOOK_PATH.read_text())
    rel = {r["record_id"]: r for r in read_jsonl(config.PROCESSED_DIR / "relevant.jsonl")}
    out = []
    for row in csv.DictReader(open(config.OUTPUT_DIR / "golden_set_labelled.csv", encoding="utf-8")):
        rid = row["record_id"]
        cached = llm.cache_get("extract_gemini", rid, config.PROMPT_VERSION_EXTRACT)
        if cached is None:
            cached = s4_extract.extract(rel[rid], cb)
            cached["model"] = config.MODEL_EXTRACT
            llm.cache_put("extract_gemini", rid, config.PROMPT_VERSION_EXTRACT, cached)
        out.append(cached)
    from sip.common import write_jsonl
    write_jsonl(config.PROCESSED_DIR / "extractions_gemini_golden.jsonl", out)
    spans = [t["verified"] for x in out if x["status"] == "ok" for t in x["themes"]]
    print(f"gemini: {len(out)} records, {sum(x['status'] != 'ok' for x in out)} malformed, "
          f"{sum(x.get('attempts', 1) > 1 for x in out)} needed retry, theme spans verified {sum(spans)}/{len(spans)}")
    score("extractions_gemini_golden.jsonl", "_gemini")


if __name__ == "__main__":
    {"blank": blank, "score": score, "gemini": gemini}[sys.argv[1] if len(sys.argv) > 1 else "blank"]()
