# SIP Discovery Engine (Groww Growth, Part 1)

Finds **why first-time mutual-fund investors pause or stop SIPs**, using public feedback.
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
| 3 Open coding + codebook | *(next)* | `codebook.yaml` (hand-curated) |
| 4 Extract | `python s4_extract.py` | `data/processed/extractions.jsonl`, `outputs/span_check_stats.json` |
| 5-8 | *(to come: aggregate/score, validate, report, Streamlit app)* | |

Tests: `python -m pytest -q tests`

## Sources
Google Play (Groww), Apple App Store (Groww, India; public RSS feed, falling back to the ~10 reviews embedded
in the public app page; Apple's token-gated review API is not used), YouTube Data API v3 comments,
TradingQ&A (public Discourse JSON). **Reddit is out** (API access needs approval; scraping is barred).
Usernames are stored only as one-way hashes.

## Corrections
Every time a human rejects or corrects AI output, add an entry to `corrections_log.md`.
