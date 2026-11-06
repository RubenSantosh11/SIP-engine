"""Every model name, limit and path for the pipeline lives here, so they are easy to change.

Free-tier limits change often, so the numbers below are deliberately conservative.
Raise them only after checking your quota in AI Studio.
"""
import os
from pathlib import Path

ROOT = Path(__file__).parent
ON_VERCEL = bool(os.environ.get("VERCEL"))  # the deployed "Try it" app
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
# Vercel's filesystem is read-only except /tmp
CACHE_DIR = Path("/tmp/sip/cache") if ON_VERCEL else ROOT / "data" / "cache"
STATE_DIR = Path("/tmp/sip/state") if ON_VERCEL else ROOT / "data" / "state"
OUTPUT_DIR = ROOT / "outputs"

# ---- LLM provider ----
# "session": prompts are written to data/session/requests/ and answered by Claude (Opus) inside a
#            Claude Code session; answers land in data/session/answers/. No API key needed.
# "gemini":  the Gemini REST API (needs GEMINI_API_KEY with available quota or credits).
LLM_PROVIDER = os.environ.get("SIP_LLM_PROVIDER", "gemini" if ON_VERCEL else "session")
SESSION_DIR = ROOT / "data" / "session"
SESSION_MODEL_LABEL = "claude-opus (Claude Code session)"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MODEL_FILTER = "gemini-3.5-flash-lite"   # Stage 2 relevance filter (batched)
MODEL_EXTRACT = "gemini-3.8-flash"       # Stage 3 open coding + Stage 4 extraction
TEMPERATURE = 0.0

# Daily request budget per model, counted locally in data/state/llm_usage.json.
# The pipeline stops cleanly when the budget is hit; re-run tomorrow to resume.
DAILY_REQUEST_BUDGET = {
    MODEL_FILTER: 400,
    MODEL_EXTRACT: 300 if ON_VERCEL else 200,
}
MIN_SECONDS_BETWEEN_CALLS = 0.0 if ON_VERCEL else 6.0   # pipeline: about 10 requests per minute
MAX_RETRIES = 1 if ON_VERCEL else 5                      # on 429 / 5xx
BACKOFF_BASE_SECONDS = 2.0 if ON_VERCEL else 4.0         # pipeline: 4, 8, 16, 32, 64 s
REQUEST_TIMEOUT_SECONDS = 25 if ON_VERCEL else 90

# Bump a version whenever its prompt changes; cached results are keyed by record_id + version.
PROMPT_VERSION_FILTER = "filter-v2"
PROMPT_VERSION_OPENCODE = "opencode-v1"
PROMPT_VERSION_EXTRACT = "extract-v2"

FILTER_BATCH_SIZE = 10

# ---- Collection ----
# Apps whose public store reviews we collect. Groww is the focus; the others widen coverage of
# first-time SIP investing in India (why people discontinue is not platform-specific).
PLAY_APPS = {
    "groww": "com.nextbillion.groww",
    "coin": "com.zerodha.coin",
    "etmoney": "com.smartspends",
    "paytmmoney": "com.paytmmoney",
    "indmoney": "in.indwealth",
    "upstox": "in.upstox.app",
    "angelone": "com.msf.angelmobile",
    "fundsindia": "com.fundsindia",
}
APPSTORE_APPS = {
    "groww": "1404871703",
    "etmoney": "1212752482",
    "paytmmoney": "1344431352",
    "kuvera": "1329701793",
    "indmoney": "1450178837",
    "upstox": "1584953620",
    "angelone": "1060530981",
}
PLAY_REVIEWS_PER_APP = {"groww": 8000}   # others use PLAY_REVIEWS_DEFAULT
PLAY_REVIEWS_DEFAULT = 4000
APPSTORE_COUNTRY = "in"
HTTP_USER_AGENT = "SIP-discovery-research/0.1 (Nextleap student project; polite, low volume)"
POLITE_DELAY_SECONDS = 1.0

# Thin slice: per-source caps for the first end-to-end run (aims for ~50 relevant records).
THIN_SLICE_PER_SOURCE = {"playstore": 300, "appstore": 50, "youtube": 300, "tradingqna": 80}

# Research questions (drive the filter, open coding and codebook "question" tags):
#   start     - Why do people start a SIP, and what do they expect to happen?
#   behaviour - What changes in their behaviour in the months after starting?
#   stop      - What leads investors to pause, reduce or stop a SIP?

# Full-run targets. Play Store reviews rarely mention SIPs, so we pull many and let the free
# keyword pre-filter keep the SIP ones.
TARGET_PER_SOURCE = {
    "playstore": None,    # per app: PLAY_REVIEWS_PER_APP / PLAY_REVIEWS_DEFAULT
    "appstore": 500,      # per app; public RSS feed returns at most 500 recent reviews
    "youtube": 2200,
    "tradingqna": 500,
}

# YouTube Data API v3 default quota is 10,000 units/day.
# search.list = 100 units per call, commentThreads.list = 1 unit per page.
YOUTUBE_SEARCH_QUERIES = [
    # stop / pause / reduce
    "stopped my SIP",
    "should I stop my SIP",
    "SIP pause or stop market crash",
    "why people stop SIP",
    # start / expectations
    "why I started SIP",
    "my first SIP mutual fund experience",
    "SIP returns expectation beginners",
    "Groww SIP mutual fund beginners",
    # behaviour after starting / continuing
    "SIP 1 year experience returns",
    "continued SIP during market crash",
    "10 years of SIP journey",
    "SIP negative returns what to do",
    # first-year discontinuation (added after the first full run)
    "stopped SIP after 1 year",
    "SIP band kar diya kyun",
    "first year SIP loss beginner",
    "mutual fund SIP mistakes I made",
]
YOUTUBE_VIDEOS_PER_QUERY = 8
YOUTUBE_DAILY_UNIT_BUDGET = 3000  # well below the 10k default

TRADINGQNA_SEARCH_QUERIES = [
    "stop sip", "pause sip", "sip stopped", "sip cancel", "skip sip", "sip missed",
    "continue sip", "sip mandate", "reduce sip", "sip loss", "groww sip",
    "started sip", "first sip", "sip returns", "increase sip", "step up sip", "sip negative returns",
]
TRADINGQNA_MAX_TOPICS_PER_QUERY = 12

# ValuePickr (Discourse). Its robots.txt disallows /search, so we list topics in these
# categories via the public category JSON and keep those whose titles mention SIPs / mutual funds.
VALUEPICKR_CATEGORIES = {9: "investing-strategies", 12: "q-a-questions-answers", 1: "uncategorized",
                         72: "investment-journey", 44: "behavourial-management", 58: "newbies-must-read",
                         32: "learning", 8: "lessons-from-mr-market"}
VALUEPICKR_TITLE_TERMS = r"\bsips?\b|mutual fund|\bmfs?\b|index fund|systematic|monthly invest"
VALUEPICKR_MAX_PAGES_PER_TOPIC = 3
FORUM_TARGET = {"tradingqna": 500, "valuepickr": 500}

# ---- Stage 2 keyword pre-filter ----
SIP_TERMS = [
    r"\bsips?\b", r"systematic investment", r"auto[- ]?pay", r"auto[- ]?debit",
    r"auto[- ]?invest", r"monthly invest", r"invest(?:ing)? (?:every|each) month",
    r"\bmandates?\b", r"\bnach\b", r"recurring invest",
]
# Used only when SIPs appear in the context (video/topic title) but not in the text itself.
ACTION_TERMS = [
    r"stop", r"paus", r"cancel", r"skip", r"miss", r"continu", r"discontinu",
    r"\bquit", r"halt", r"break", r"resum", r"redeem", r"withdr", r"bounc",
    r"fail", r"\bband\b", r"\bclos", r"exit", r"sell", r"\bleft\b", r"leave",
    r"reduc", r"decreas", r"increas", r"step[- ]?up", r"\bstart", r"began", r"begin",
    r"first", r"expect", r"return", r"profit", r"loss", r"\bred\b", r"negative",
]

# ---- Stage 4/5 ----
# A theme is ranked only if at least MIN_THEME_RECORDS records mention it, from at least
# MIN_THEME_SOURCES different sources; otherwise it is listed separately as "too little evidence".
MIN_THEME_RECORDS = 30
MIN_THEME_SOURCES = 2
# Which sip_status values count as droppers vs continuers in the stop-lift contrast.
DROPPER_STATUSES = ["stopped", "paused", "reduced"]
CONTINUER_STATUSES = ["continuing"]
# Records whose only "stop" is switching plan/platform (e.g. regular -> direct) are not droppers;
# the codebook marks such themes with exclude_from_droppers: true.
MAX_ONE_LINE_REASON_WORDS = 20

# ---- Streamlit "Try it" tab ----
APP_MAX_INPUT_CHARS = 2000
APP_MIN_INPUT_CHARS = 15
APP_MAX_CALLS_PER_IP_PER_HOUR = 10       # best effort: counted per serverless instance
APP_DAILY_REQUEST_BUDGET = 300           # Gemini requests per day per instance; billing alert is the real backstop

CODEBOOK_PATH = ROOT / "codebook.yaml"
