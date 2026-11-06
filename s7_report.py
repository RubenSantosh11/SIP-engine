"""Stage 7: results exports (CSV + markdown) and the Evidence Log draft. Pure Python, no LLM calls.

Reads the stage outputs and writes:
  outputs/sources_volume.csv     raw / keyword-pass / relevant / extracted per source
  outputs/top_quotes.csv         3 verbatim quotes per ranked theme (different sources where possible)
  outputs/report_data.json       everything the results page needs
  outputs/results.md             ranked themes, contrast table, quotes, validation, limitations
  outputs/evidence_log.md        sources and volume, golden set, corrections, limitations
"""
import csv
import json
from collections import Counter, defaultdict

import yaml

import config
from sip.common import read_jsonl

SOURCES = ["playstore", "appstore", "youtube", "tradingqna", "valuepickr"]
SOURCE_LABEL = {"playstore": "Google Play", "appstore": "Apple App Store", "youtube": "YouTube comments",
                "tradingqna": "TradingQ&A forum", "valuepickr": "ValuePickr forum"}

LIMITATIONS = [
    "Reddit was not used: its API needs approval and scraping is barred by its terms. X, Instagram and Quora were also not used (no permitted access).",
    "Reviews and forum posts are not a random sample of investors. App-store reviews skew towards complaints, so product friction is over-represented relative to behavioural reasons such as returns or cash needs.",
    "Droppers come mostly from app-store reviews and continuers mostly from YouTube, so stop-lift partly reflects which source a theme appears in, not only stopping behaviour. Read stop-lift as directional.",
    "SIP status, first-time status and time since starting are self-reported. Only 7 records say the writer is a first-time investor and 84 state how long they have invested, so the 12-month view is descriptive only.",
    "'Stopped' includes stopping SIPs on a platform; people who only moved to another app are excluded from the dropper group where switching was their only stop reason.",
    "Coding was done by Claude (Opus) inside a Claude Code session, not via an API, because the Gemini key had no credits. The same model designed the prompts and did the coding; the golden set is the independent check.",
    "Evidence-span checks were run by the coder before submitting answers, so the 100% span pass rate reflects that self-check; the pipeline still verifies every span in code.",
    "The second pass (what people check, worries, help outside the app, segment) only coded records containing a cue word; signals phrased without one are missed. Segment signals (age, income stability, source of money, influencer) are rarely stated in public posts: at most 9 records per value, so segment differences must come from interviews.",
    "The golden set is small (20 records), so per-field agreement has wide uncertainty.",
    "Most store reviews come from apps other than Groww (Coin, ET Money, FundsIndia, Paytm Money and others). Findings describe first-time SIP investing in India generally, not Groww specifically.",
]


def main() -> None:
    cb = yaml.safe_load(config.CODEBOOK_PATH.read_text())
    themes = {t["id"]: t for t in cb["themes"]}
    raw = {s: read_jsonl(config.RAW_DIR / f"{s}.jsonl") for s in SOURCES}
    filt = json.loads((config.OUTPUT_DIR / "filter_stats.json").read_text())
    rel = {r["record_id"]: r for r in read_jsonl(config.PROCESSED_DIR / "relevant.jsonl")}
    ex = [x for x in read_jsonl(config.PROCESSED_DIR / "extractions.jsonl") if x.get("status") == "ok"]
    ranked = list(csv.DictReader(open(config.OUTPUT_DIR / "themes_ranked.csv", encoding="utf-8")))
    contrast = list(csv.DictReader(open(config.OUTPUT_DIR / "contrast_table.csv", encoding="utf-8")))
    scoring = json.loads((config.OUTPUT_DIR / "scoring_summary.json").read_text())
    spans = json.loads((config.OUTPUT_DIR / "span_check_stats.json").read_text())
    val_path = config.OUTPUT_DIR / "validation_summary.json"
    validation = json.loads(val_path.read_text()) if val_path.exists() else None
    gem_path = config.OUTPUT_DIR / "validation_summary_gemini.json"
    validation_gemini = json.loads(gem_path.read_text()) if gem_path.exists() else None
    failures = list(csv.DictReader(open(config.OUTPUT_DIR / "validation_failures.csv", encoding="utf-8"))) \
        if (config.OUTPUT_DIR / "validation_failures.csv").exists() else []

    # Sources and volume
    volume = []
    for s in SOURCES:
        f = filt.get(s, {})
        apps = Counter(r.get("app") for r in raw[s] if r.get("app"))
        volume.append({"source": s, "label": SOURCE_LABEL[s], "raw": len(raw[s]), "pass_keyword": f.get("pass_prefilter", 0),
                       "relevant": f.get("kept", 0), "extracted": sum(x["source"] == s for x in ex),
                       "apps": dict(apps), "dates": [min((r["date"] for r in raw[s] if r.get("date")), default=None),
                                                     max((r["date"] for r in raw[s] if r.get("date")), default=None)]})
    with open(config.OUTPUT_DIR / "sources_volume.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "raw", "pass_keyword_filter", "relevant", "extracted", "earliest", "latest"])
        for v in volume:
            w.writerow([v["label"], v["raw"], v["pass_keyword"], v["relevant"], v["extracted"], *v["dates"]])

    # Quotes: 3 per theme, highest severity first, spread across sources, verified spans only
    hits = defaultdict(list)
    for x in ex:
        for t in x["themes"]:
            if t.get("verified"):
                hits[t["theme_id"]].append((t["severity"], x["record_id"], x["source"], t["evidence_span"]))
    quotes = {}
    for tid, hs in hits.items():
        hs.sort(key=lambda h: (-h[0], -len(h[3])))
        picked, used = [], set()
        for h in hs:  # first pass: one per source
            if h[2] not in used and len(h[3]) >= 25:
                picked.append(h)
                used.add(h[2])
            if len(picked) == 3:
                break
        for h in hs:
            if len(picked) == 3:
                break
            if h not in picked and len(h[3]) >= 25:
                picked.append(h)
        quotes[tid] = [{"quote": h[3], "source": SOURCE_LABEL[h[2]], "app": rel[h[1]].get("app"),
                        "url": rel[h[1]].get("url"), "record_id": h[1], "severity": h[0]} for h in picked]
    with open(config.OUTPUT_DIR / "top_quotes.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["theme_id", "quote", "source", "app", "record_id"])
        for r in ranked:
            for q in quotes.get(r["theme_id"], []):
                w.writerow([r["theme_id"], q["quote"], q["source"], q["app"] or "", q["record_id"]])

    # 12-month view (descriptive): records stating < 12 months since start
    early = [x for x in ex if x.get("time_since_start") in ("<1m", "1-6m", "6-12m") and x.get("time_since_start_verified")]
    early_themes = Counter(t["theme_id"] for x in early for t in x["themes"] if t.get("verified"))
    first_time = [x for x in ex if x.get("first_time_investor") == "yes"]

    context = list(csv.DictReader(open(config.OUTPUT_DIR / "context_summary.csv", encoding="utf-8"))) \
        if (config.OUTPUT_DIR / "context_summary.csv").exists() else []
    context_stats = json.loads((config.OUTPUT_DIR / "context_stats.json").read_text()) \
        if (config.OUTPUT_DIR / "context_stats.json").exists() else None
    status = Counter(x["sip_status"] for x in ex)
    corrections = [l for l in (config.ROOT / "corrections_log.md").read_text().splitlines()
                   if l.startswith("| 20")]
    data = {
        "volume": volume, "totals": {k: sum(v[k] for v in volume) for k in ["raw", "pass_keyword", "relevant", "extracted"]},
        "status": dict(status), "scoring": scoring, "span_check": spans,
        "ranked": ranked, "contrast": contrast, "quotes": quotes,
        "themes": {tid: {"name": t["name"], "definition": t["definition"], "question": t.get("question"),
                         "addressability": t["addressability"]} for tid, t in themes.items()},
        "early": {"n": len(early), "themes": early_themes.most_common()},
        "first_time_n": len(first_time),
        "validation": validation, "validation_gemini": validation_gemini, "validation_failures": failures,
        "corrections": [[c.strip() for c in l.strip("|").split("|")] for l in corrections],
        "context": context, "context_stats": context_stats,
        "limitations": LIMITATIONS, "addressability_scores": cb["addressability_scores"],
    }
    (config.OUTPUT_DIR / "report_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    # Same data for the deployed site (public/): aggregates, public quotes and record ids only
    (config.ROOT / "public" / "data").mkdir(parents=True, exist_ok=True)
    (config.ROOT / "public" / "data" / "report_data.json").write_text(json.dumps(data, ensure_ascii=False))
    write_markdown(data)
    print("wrote report_data.json, results.md, evidence_log.md, sources_volume.csv, top_quotes.csv")


def pct(x) -> str:
    return f"{100 * float(x):.0f}%"


def write_markdown(d: dict) -> None:
    elig = [r for r in d["ranked"] if r["eligible"] == "True"]
    excl = [r for r in d["ranked"] if r["eligible"] != "True"]
    L = ["# SIP Discovery Engine: results", "",
         "Why first-time SIP investors in India pause, reduce or stop. Public feedback, coded one record at a time; all counting and scoring in Python.", "",
         "## Sources and volume", "", "| Source | Raw | Passed keyword filter | Relevant | Extracted |", "|---|---|---|---|---|"]
    for v in d["volume"]:
        L.append(f"| {v['label']} | {v['raw']:,} | {v['pass_keyword']:,} | {v['relevant']:,} | {v['extracted']:,} |")
    t = d["totals"]
    L += [f"| **Total** | **{t['raw']:,}** | **{t['pass_keyword']:,}** | **{t['relevant']:,}** | **{t['extracted']:,}** |", "",
          f"SIP status of extracted records: {', '.join(f'{k} {v}' for k, v in sorted(d['status'].items(), key=lambda kv: -kv[1]))}. "
          f"Dropper group: {d['scoring']['n_droppers']} records; continuer group: {d['scoring']['n_continuers']}.", "",
          "## Ranked opportunity areas", "",
          f"Ranked by the lower confidence bound of priority = reach x severity x stop-lift x addressability. A theme is ranked only with at least {d['scoring']['min_theme_records']} records from at least {d['scoring']['min_theme_sources']} sources.", "",
          "| # | Theme | Records | Reach (95% CI) | Severity | Stop-lift (95% CI) | Addressability | Priority (low bound) |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(elig, 1):
        lift = "guarded" if r["lift_guarded"] == "True" else f"{float(r['stop_lift']):.1f} ({float(r['stop_lift_low']):.1f}-{float(r['stop_lift_high']):.1f})"
        L.append(f"| {i} | {r['name']} | {r['n_records']} | {pct(r['reach'])} ({pct(r['reach_low'])}-{pct(r['reach_high'])}) | "
                 f"{float(r['severity']):.1f} | {lift} | {r['addressability']} | {float(r['priority_low']):.3f} |")
    L += ["", "**Not ranked**", "", "| Theme | Records | Reason |", "|---|---|---|"]
    for r in excl:
        L.append(f"| {r['name']} | {r['n_records']} | {r['excluded_reason']} |")
    L += ["", "## Droppers vs continuers", "", "| Theme | Droppers mentioning | Continuers mentioning | Stop-lift |", "|---|---|---|---|"]
    for c in d["contrast"]:
        L.append(f"| {c['name']} | {c['droppers_mentioning']}/{c['n_droppers']} ({pct(c['pct_droppers'])}) | "
                 f"{c['continuers_mentioning']}/{c['n_continuers']} ({pct(c['pct_continuers'])}) | {c['stop_lift']} |")
    L += ["", "## Quotes for each ranked theme", ""]
    for r in elig:
        L.append(f"**{r['name']}**")
        for q in d["quotes"].get(r["theme_id"], []):
            L.append(f"- \"{q['quote']}\" ({q['source']}{', ' + q['app'] if q['app'] else ''})")
        L.append("")
    L += ["## Within the first 12 months (descriptive)", "",
          f"{d['early']['n']} records state that the writer started less than 12 months ago; {d['first_time_n']} say they are first-time investors. Too few to score; most frequent themes among them:", ""]
    for tid, n in d["early"]["themes"][:6]:
        L.append(f"- {d['themes'].get(tid, {}).get('name', tid)}: {n}")
    L += ["", "## What investors check, worry about, and where they turn", "",
          "Second extraction pass. Only records containing a cue word were coded (the rest were set empty by rule), so counts are a floor. Records counted once per value.", "",
          "| Question | Value | Records | Stopped/paused | Still investing |", "|---|---|---|---|---|"]
    for c in d["context"]:
        if c["field"] != "check_frequency":
            L.append(f"| {c['field']} | {c['value']} | {c['records_all']} | {c['records_dropper']} | {c['records_continuer']} |")
    L += ["", "## Validation", ""] + validation_md(d) + ["", "## Limitations", ""] + [f"- {x}" for x in d["limitations"]]
    (config.OUTPUT_DIR / "results.md").write_text("\n".join(L) + "\n")

    E = ["# AI Evidence Log: SIP Discovery Engine", "", "## 1. Sources and volume analysed", "",
         "| Source | Raw records | Relevant | Notes |", "|---|---|---|---|"]
    for v in d["volume"]:
        apps = ", ".join(f"{a} {n:,}" for a, n in sorted(v["apps"].items(), key=lambda kv: -kv[1])) if v["apps"] else ""
        E.append(f"| {v['label']} | {v['raw']:,} | {v['relevant']:,} | {apps} |")
    E += [f"| **Total** | **{t['raw']:,}** | **{t['relevant']:,}** | |", "",
          "Pipeline: collect (public data, usernames stored only as hashes) -> keyword filter -> relevance check in batches of 10 -> open coding of 100 records -> codebook curated by the PM -> structured extraction of every relevant record with verbatim evidence -> scoring in Python.", "",
          "## 2. Golden set", "",
          "20 records drawn at random before extraction (fixed seed), stratified across sources and apps, excluding any record whose engine output the PM had already seen. The PM labelled them by hand without seeing engine output.", ""]
    E += validation_md(d)
    E += ["", "## 3. Where AI output was rejected or corrected", "", "| Date | Stage | What the AI said | What changed | Why |", "|---|---|---|---|---|"]
    for c in d["corrections"]:
        E.append("| " + " | ".join(c) + " |")
    E += ["", "## 4. Limitations", ""] + [f"- {x}" for x in d["limitations"]]
    (config.OUTPUT_DIR / "evidence_log.md").write_text("\n".join(E) + "\n")


VAL_ROWS = [("sip_status", "SIP status"), ("first_time_investor", "First-time investor"),
            ("time_since_start", "Time since starting"), ("severity_within_1", "Severity within ±1")]


def validation_md(d: dict) -> list[str]:
    s = d["span_check"]
    out = [f"Evidence-span check: {s['coded_values_with_span']} coded values, {s['span_failures_after_retry']} failures, pass rate {pct(s['span_pass_rate'])}.", ""]
    v, g = d["validation"], d.get("validation_gemini")
    if not v:
        return out + ["Golden-set agreement: pending. The PM is labelling `outputs/golden_set_blank.csv`."]
    cell = lambda x, f: (f"{x['agreement'][f]['agree']}/{x['agreement'][f]['n']} ({x['agreement'][f]['pct']:.0f}%)"
                         if x and f in x["agreement"] and x["agreement"][f]["pct"] is not None else "—")
    out += ["Agreement with the PM's hand labels on 20 records:", "",
            "| Field | Pipeline engine (Claude, session) | Deployed model (Gemini Flash) |", "|---|---|---|"]
    for f, label in VAL_ROWS:
        out.append(f"| {label} | {cell(v, f)} | {cell(g, f)} |")
    pr = lambda x, k: f"{100 * x[k]:.0f}%" if x and x.get(k) is not None else "—"
    out += [f"| Theme precision (engine themes the PM also chose) | {pr(v, 'theme_precision')} | {pr(g, 'theme_precision')} |",
            f"| Theme recall (PM themes the engine also chose) | {pr(v, 'theme_recall')} | {pr(g, 'theme_recall')} |",
            f"| Records whose theme sets overlap | {v.get('records_theme_overlap', '—')}/20 | {g.get('records_theme_overlap', '—') if g else '—'}/20 |", ""]
    if d["validation_failures"]:
        from collections import Counter
        causes = Counter(f["likely_cause"] for f in d["validation_failures"])
        out += ["Where the pipeline engine disagreed, by likely cause:", "", "| Likely cause | Disagreements |", "|---|---|"]
        out += [f"| {c} | {n} |" for c, n in causes.most_common()]
        out += ["", "Every disagreement:", "", "| Record | Field | PM label | Engine | Likely cause |", "|---|---|---|---|---|"]
        for f in d["validation_failures"]:
            out.append(f"| {f['record_id']} | {f['field']} | {f['my_label']} | {f['engine_output']} | {f['likely_cause']} |")
    return out


if __name__ == "__main__":
    main()
