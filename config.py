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

# ---- LLM provider (Gemini REST API) ----
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
PROMPT_VERSION_FILTER = "filter-v1"
PROMPT_VERSION_OPENCODE = "opencode-v1"
PROMPT_VERSION_EXTRACT = "extract-v1"

FILTER_BATCH_SIZE = 10

# ---- Collection ----
GROWW_PLAY_ID = "com.nextbillion.groww"
GROWW_APPSTORE_ID = "1404871703"
APPSTORE_COUNTRY = "in"
HTTP_USER_AGENT = "SIP-discovery-research/0.1 (Nextleap student project; polite, low volume)"
POLITE_DELAY_SECONDS = 1.0

# Thin slice: the first end-to-end run caps each source at this many records.
THIN_SLICE_PER_SOURCE = 15

# Full-run targets (about 2,500 raw records in total)
TARGET_PER_SOURCE = {
    "playstore": 900,
    "appstore": 500,      # the public RSS feed returns at most 500 recent reviews
    "youtube": 800,
    "tradingqna": 400,
}

# YouTube Data API v3 default quota is 10,000 units/day.
# search.list = 100 units per call, commentThreads.list = 1 unit per page.
YOUTUBE_SEARCH_QUERIES = [
    "stopped my SIP",
    "should I stop my SIP",
    "SIP pause or stop market crash",
    "Groww SIP mutual fund beginners",
    "why people stop SIP",
    "SIP mistakes beginners India",
]
YOUTUBE_VIDEOS_PER_QUERY = 8
YOUTUBE_MAX_COMMENT_PAGES_PER_VIDEO = 3
YOUTUBE_DAILY_UNIT_BUDGET = 3000  # well below the 10k default

TRADINGQNA_SEARCH_QUERIES = [
    "stop sip", "pause sip", "sip stopped", "sip cancel", "skip sip",
    "sip missed", "continue sip", "sip mandate", "sip loss", "groww sip",
]
TRADINGQNA_MAX_TOPICS_PER_QUERY = 15

# ---- Stage 2 keyword pre-filter ----
SIP_TERMS = [
    r"\bsips?\b", r"systematic investment", r"auto[- ]?pay", r"auto[- ]?debit",
    r"auto[- ]?invest", r"monthly invest", r"invest(?:ing)? (?:every|each) month",
    r"\bmandates?\b", r"\bnach\b", r"recurring invest",
]
ACTION_TERMS = [
    r"stop", r"paus", r"cancel", r"skip", r"miss", r"continu", r"discontinu",
    r"\bquit", r"halt", r"break", r"resum", r"redeem", r"withdr", r"bounc",
    r"fail", r"\bband\b", r"\bclos", r"exit", r"sell", r"left", r"leave",
]

# ---- Stage 4 extraction ----
MAX_ONE_LINE_REASON_WORDS = 20

# ---- Streamlit "Try it" tab ----
APP_MAX_INPUT_CHARS = 2000
APP_MAX_CALLS_PER_SESSION = 5
APP_MIN_SECONDS_BETWEEN_CALLS = 20

CODEBOOK_PATH = ROOT / "codebook.yaml"
