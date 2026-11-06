# SIP Discovery Engine (Groww Growth, Part 1)

Uses public feedback to answer three questions about SIP investors:
1. **Start**: why do people start a SIP, and what do they expect to happen?
2. **Behaviour**: what changes in their behaviour in the months after starting?
3. **Stop**: what leads investors to pause, reduce or stop a SIP?

Design rule: **structured extraction, not summarisation**. The LLM fills a typed schema for one record
at a time, with a verbatim evidence quote for every coded value (checked in code). All counting, scoring
and ranking is plain Python. No fund/stock recommendations, no fear/FOMO/urgency language.

## Setup
```bash
pip install -r requirements.txt
```
Keys come from environment variables (or a local `.env`, never committed): `YOUTUBE_API_KEY`;
`GEMINI_API_KEY` only if `LLM_PROVIDER = "gemini"` in `config.py`.

## LLM provider
All model calls go through `sip/llm.py::llm_call`. `config.LLM_PROVIDER`:
- `"session"` (current): prompts are queued in `data/session/requests/`; Claude, working in a Claude Code
  session, writes JSON answers to `data/session/answers/` (`python session_queue.py status|show|answer`).
  Re-running a stage ingests the answers, validates them with pydantic and runs the span checks.
- `"gemini"`: Gemini REST API with a daily request budget, backoff on 429/5xx and a clean stop when the
  quota is exhausted. (As of Oct 2026 the provided key's project had no credits.)

Every result is cached per `record_id` + prompt version in `data/cache/`, so re-running never repeats work.

## Run order
| Stage | Command | Output |
|---|---|---|
| 1 Collect | `python collect_playstore.py`, `collect_appstore.py`, `collect_youtube.py`, `collect_tradingqna.py` (add `--thin` for the thin slice) | `data/raw/*.jsonl` (gitignored) |
| 2 Relevance filter | `python s2_filter.py` | `data/processed/relevant.jsonl`, `outputs/filter_stats.json` |
| 3 Open coding + codebook | `python s3_open_code.py` | `outputs/open_codes.jsonl`, `codebook_draft.yaml` -> you curate `codebook.yaml` |
| 4 Extract | `python s4_extract.py` | `data/processed/extractions.jsonl`, `outputs/span_check_stats.json` |
| 5 Score | `python s5_aggregate.py` | `outputs/themes_ranked.csv`, `outputs/contrast_table.csv` |
| 6 Validate | `python s6_validate.py blank` (before extraction), PM labels, then `python s6_validate.py score` | `outputs/golden_set_*.csv`, `outputs/validation_summary.json` |
| 7 Report | `python s7_report.py` then `python s7_dashboard_csvs.py` | `outputs/results.md`, `outputs/evidence_log.md`, `outputs/dashboard/*.csv` (results page data) |

## Scoring (Stage 5)
- **reach**: share of records with a clear SIP status (dropper or continuer) that mention the theme via a verified quote; 95% Wilson interval.
- **severity**: mean of 1-3 severities of verified mentions.
- **stop-lift**: risk ratio P(theme | stopped/paused/reduced) / P(theme | continuing), Katz log 95% interval, 0.5 continuity correction for zero cells; set to 1 (neutral) if either group has < 10 records or the theme < 5 mentions. Records whose only stop theme is switching are not droppers.
- **addressability**: codebook tag mapped high 1.0, medium 0.6, low 0.3.
- **priority** = reach x severity x stop-lift x addressability; ranked by the lower bound (reach_low x severity x lift_low x addressability).
- Ranked only with >= 30 records from >= 2 sources (`config.py`); contrast-only and switching themes are never ranked.

Tests: `python -m pytest -q tests`

## Sources
Google Play (Groww), Apple App Store (Groww, India; public RSS feed, falling back to the ~10 reviews embedded
in the public app page; Apple's token-gated review API is not used), YouTube Data API v3 comments,
TradingQ&A (public Discourse JSON). **Reddit is out** (API access needs approval; scraping is barred).
Usernames are stored only as one-way hashes.

## Corrections
Every time a human rejects or corrects AI output, add an entry to `corrections_log.md`.
