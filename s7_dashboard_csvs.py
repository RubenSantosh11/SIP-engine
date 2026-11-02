"""Write the CSV files the results dashboard reads (outputs/dashboard/*.csv) from outputs/report_data.json."""
import csv
import json

import config

OUT = config.OUTPUT_DIR / "dashboard"


def write(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main() -> None:
    d = json.loads((config.OUTPUT_DIR / "report_data.json").read_text())
    write("volume", ["source", "raw", "pass_keyword_filter", "relevant", "extracted"],
          [[v["label"], v["raw"], v["pass_keyword"], v["relevant"], v["extracted"]] for v in d["volume"]])
    rank = 0
    rows = []
    for r in d["ranked"]:
        ranked = r["eligible"] == "True"
        rank += ranked
        rows.append([rank if ranked else "", r["theme_id"], r["name"], r["question"], r["n_records"],
                     r["reach"], r["reach_low"], r["reach_high"], r["severity"],
                     "" if r["lift_guarded"] == "True" else r["stop_lift"],
                     "" if r["lift_guarded"] == "True" else r["stop_lift_low"],
                     "" if r["lift_guarded"] == "True" else r["stop_lift_high"],
                     r["addressability"], r["priority_low"], "ranked" if ranked else "not ranked",
                     r["excluded_reason"] or ""])
    write("themes", ["rank", "theme_id", "theme", "question", "records", "reach", "reach_low", "reach_high", "severity",
                     "stop_lift", "stop_lift_low", "stop_lift_high", "addressability", "priority_low", "status", "reason"], rows)
    write("contrast", ["theme_id", "theme", "droppers_mentioning", "n_droppers", "pct_droppers",
                       "continuers_mentioning", "n_continuers", "pct_continuers"],
          [[c["theme_id"], c["name"], c["droppers_mentioning"], c["n_droppers"], c["pct_droppers"],
            c["continuers_mentioning"], c["n_continuers"], c["pct_continuers"]] for c in d["contrast"]])
    names = {r["theme_id"]: r["name"] for r in d["ranked"]}
    write("quotes", ["quote_id", "theme_id", "theme", "quote", "source", "app"],
          [[f"{tid}-{i}", tid, names[tid], q["quote"], q["source"], q["app"] or ""]
           for r in d["ranked"] if r["eligible"] == "True" for tid in [r["theme_id"]]
           for i, q in enumerate(d["quotes"].get(tid, []), 1)])
    write("early", ["theme_id", "theme", "records"], [[t, names.get(t, t), n] for t, n in d["early"]["themes"]])
    s = d["span_check"]
    write("summary", ["metric", "value"], [
        ["raw_records", d["totals"]["raw"]], ["relevant_records", d["totals"]["relevant"]],
        ["extracted_records", d["totals"]["extracted"]], ["droppers", d["scoring"]["n_droppers"]],
        ["continuers", d["scoring"]["n_continuers"]], ["first_time_stated", d["first_time_n"]],
        ["started_within_12m", d["early"]["n"]], ["coded_values", s["coded_values_with_span"]],
        ["span_failures", s["span_failures_after_retry"]], ["span_pass_rate", s["span_pass_rate"]],
        ["golden_labelled", (d["validation"] or {}).get("n_labelled", 0)]])
    v = d["validation"]
    vrows = []
    if v:
        for f in ["sip_status", "first_time_investor", "time_since_start", "severity_within_1"]:
            if f in v["agreement"]:
                a = v["agreement"][f]
                vrows.append([f, a["agree"], a["n"], a["pct"] / 100 if a["pct"] is not None else ""])
        th = [a for k, a in v["agreement"].items() if k.startswith("theme:")]
        vrows.append(["theme_present_absent", sum(a["agree"] for a in th), sum(a["n"] for a in th),
                      v["theme_presence_overall_pct"] / 100 if v["theme_presence_overall_pct"] is not None else ""])
    write("validation", ["field", "agree", "n", "pct"], vrows)
    write("failures", ["failure_id", "record_id", "field", "pm_label", "engine_output", "likely_cause"],
          [[i, f["record_id"], f["field"], f["my_label"], f["engine_output"], f["likely_cause"]]
           for i, f in enumerate(d["validation_failures"], 1)])
    write("corrections", ["entry", "date", "stage", "ai_said", "changed_to", "why"],
          [[i, *c[:5]] for i, c in enumerate(d["corrections"], 1)])
    print("wrote", sorted(p.name for p in OUT.glob("*.csv")))


if __name__ == "__main__":
    main()
