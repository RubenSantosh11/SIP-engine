"""Every model name, limit and path for the pipeline lives here, so they are easy to change.

Free-tier limits change often, so the numbers below are deliberately conservative.
Raise them only after checking your quota in AI Studio.
"""
from pathlib import Path

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
CACHE_DIR = ROOT / "data" / "cache"
STATE_DIR = ROOT / "data" / "state"
OUTPUT_DIR = ROOT / "outputs"

# ---- LLM provider ----
# "session": prompts are written to data/session/requests/ and answered by Claude (Opus) inside a
#            Claude Code session; answers land in data/session/answers/. No API key needed.
# "gemini":  the Gemini REST API (needs GEMINI_API_KEY with available quota or credits).
LLM_PROVIDER = "session"
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
    MODEL_EXTRACT: 200,
}
MIN_SECONDS_BETWEEN_CALLS = 6.0   # about 10 requests per minute, under typical free-tier RPM
MAX_RETRIES = 5                   # on 429 / 5xx
BACKOFF_BASE_SECONDS = 4.0        # 4, 8, 16, 32, 64 s
REQUEST_TIMEOUT_SECONDS = 90

# Bump a version whenever its prompt changes; cached results are keyed by record_id + version.
PROMPT_VERSION_FILTER = "filter-v2"
PROMPT_VERSION_OPENCODE = "opencode-v1"
PROMPT_VERSION_EXTRACT = "extract-v2"

FILTER_BATCH_SIZE = 10

# ---- Collection ----
GROWW_PLAY_ID = "com.nextbillion.groww"
GROWW_APPSTORE_ID = "1404871703"
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
    "playstore": 8000,
    "appstore": 500,      # public RSS feed: at most 500 recent reviews (often returns none)
    "youtube": 1500,
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
]
YOUTUBE_VIDEOS_PER_QUERY = 8
YOUTUBE_DAILY_UNIT_BUDGET = 3000  # well below the 10k default

TRADINGQNA_SEARCH_QUERIES = [
    "stop sip", "pause sip", "sip stopped", "sip cancel", "skip sip", "sip missed",
    "continue sip", "sip mandate", "reduce sip", "sip loss", "groww sip",
    "started sip", "first sip", "sip returns", "increase sip", "step up sip", "sip negative returns",
]
TRADINGQNA_MAX_TOPICS_PER_QUERY = 12

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
# Which sip_status values count as droppers vs continuers in the stop-lift contrast.
DROPPER_STATUSES = ["stopped", "paused", "reduced"]
CONTINUER_STATUSES = ["continuing"]
# Records whose only "stop" is switching plan/platform (e.g. regular -> direct) are not droppers;
# the codebook marks such themes with exclude_from_droppers: true.
MAX_ONE_LINE_REASON_WORDS = 20

# ---- Streamlit "Try it" tab ----
APP_MAX_INPUT_CHARS = 2000
APP_MAX_CALLS_PER_SESSION = 5
APP_MIN_SECONDS_BETWEEN_CALLS = 20

CODEBOOK_PATH = ROOT / "codebook.yaml"
