"""Stage 5: aggregate and score themes (pure Python, deterministic; no LLM calls).

Reads data/processed/extractions.jsonl + codebook.yaml. Writes:
  outputs/themes_ranked.csv        all themes with scores, intervals and eligibility
  outputs/contrast_table.csv       share of droppers vs continuers mentioning each theme
  outputs/scoring_summary.json     group sizes and settings used
"""
import csv
import json

import yaml

import config
from sip.common import log, read_jsonl
from sip.scoring import score_themes


def main() -> None:
    codebook = yaml.safe_load(config.CODEBOOK_PATH.read_text())
    if codebook.get("status") != "final":
        log.warning("codebook status is %r (not final)", codebook.get("status"))
    records = [r for r in read_jsonl(config.PROCESSED_DIR / "extractions.jsonl") if r.get("status") == "ok"]
    rows = score_themes(records, codebook, set(config.DROPPER_STATUSES), set(config.CONTINUER_STATUSES),
                        config.MIN_THEME_RECORDS, config.MIN_THEME_SOURCES)
    config.OUTPUT_DIR.mkdir(exist_ok=True)

    cols = ["theme_id", "name", "question", "eligible", "excluded_reason", "contrast_only", "n_records", "sources",
            "reach", "reach_low", "reach_high", "severity", "stop_lift", "stop_lift_low", "stop_lift_high",
            "lift_guarded", "addressability", "addressability_score", "priority", "priority_low"]
    with open(config.OUTPUT_DIR / "themes_ranked.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "sources": ";".join(r["sources"]),
                        **{k: round(r[k], 4) for k in cols if isinstance(r.get(k), float)}})

    with open(config.OUTPUT_DIR / "contrast_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["theme_id", "name", "question", "droppers_mentioning", "n_droppers", "pct_droppers",
                    "continuers_mentioning", "n_continuers", "pct_continuers", "stop_lift"])
        for r in rows:
            pd = r["dropper_mentions"] / r["n_droppers"] if r["n_droppers"] else 0
            pc = r["continuer_mentions"] / r["n_continuers"] if r["n_continuers"] else 0
            w.writerow([r["theme_id"], r["name"], r["question"], r["dropper_mentions"], r["n_droppers"], round(pd, 3),
                        r["continuer_mentions"], r["n_continuers"], round(pc, 3),
                        "guarded" if r["lift_guarded"] else round(r["stop_lift"], 2)])

    summary = {
        "records_scored": len(records),
        "n_droppers": rows[0]["n_droppers"] if rows else 0,
        "n_continuers": rows[0]["n_continuers"] if rows else 0,
        "dropper_statuses": config.DROPPER_STATUSES, "continuer_statuses": config.CONTINUER_STATUSES,
        "min_theme_records": config.MIN_THEME_RECORDS, "min_theme_sources": config.MIN_THEME_SOURCES,
        "eligible_themes": sum(r["eligible"] for r in rows), "codebook_status": codebook.get("status"),
    }
    (config.OUTPUT_DIR / "scoring_summary.json").write_text(json.dumps(summary, indent=1))
    log.info("%s", summary)
    for r in rows:
        log.info("%-34s n=%-4d reach=%.2f [%.2f-%.2f] lift=%s prio_low=%.3f %s", r["theme_id"], r["n_records"],
                 r["reach"], r["reach_low"], r["reach_high"],
                 "guarded" if r["lift_guarded"] else f"{r['stop_lift']:.2f} [{r['stop_lift_low']:.2f}-{r['stop_lift_high']:.2f}]",
                 r["priority_low"], "" if r["eligible"] else f"EXCLUDED: {r['excluded_reason']}")


if __name__ == "__main__":
    main()
