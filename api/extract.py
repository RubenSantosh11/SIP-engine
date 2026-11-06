"""Vercel serverless function: POST /api/extract  {"text": "...", "source": "playstore|appstore|youtube|forum"}

Runs the discovery engine's Stage 4 extraction on one pasted review or comment, with the same prompt,
codebook, schema and evidence-span check as the pipeline. Quality gate and safe fallbacks:
  - declines input that does not mention SIPs / monthly investing (same keyword rule as Stage 2)
  - every quote is checked against the input in code; failing values are returned as unverified and excluded
  - malformed model output after one retry -> declines with a message instead of guessing
  - quota or rate limit -> a friendly message, never a made-up answer
The API key is read from the GEMINI_API_KEY environment variable on the server and never sent to the browser.
"""
import json
import re
import sys
import time
from collections import defaultdict, deque
from http.server import BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

import config  # noqa: E402
import s4_extract  # noqa: E402
from sip.llm import BudgetExhausted, LLMError  # noqa: E402

CODEBOOK = yaml.safe_load(config.CODEBOOK_PATH.read_text())
THEMES = {t["id"]: {"name": t["name"], "question": t.get("question")} for t in CODEBOOK["themes"]}
SIP_RE = re.compile("|".join(config.SIP_TERMS), re.I)
SOURCES = {"playstore", "appstore", "youtube", "forum"}
_hits = defaultdict(deque)

DISCLAIMER = ("This tool codes what a piece of feedback says about SIP behaviour, for research. "
              "It is not investment advice and does not recommend any fund or stock.")


def rate_limited(ip: str) -> bool:
    now, q = time.time(), _hits[ip]
    while q and now - q[0] > 3600:
        q.popleft()
    if len(q) >= config.APP_MAX_CALLS_PER_IP_PER_HOUR:
        return True
    q.append(now)
    return False


def run(text: str, source: str) -> tuple[int, dict]:
    text = (text or "").strip()
    if len(text) < config.APP_MIN_INPUT_CHARS:
        return 400, {"outcome": "declined", "message": "Paste a longer review or comment (at least a sentence)."}
    if len(text) > config.APP_MAX_INPUT_CHARS:
        return 400, {"outcome": "declined", "message": f"Please keep it under {config.APP_MAX_INPUT_CHARS} characters."}
    if not SIP_RE.search(text):
        return 200, {"outcome": "declined", "message": "This doesn't mention a SIP, auto-pay or monthly investing, so the "
                     "engine won't code it. The pipeline drops such text at the same step."}
    record = {"record_id": "try_it", "source": source if source in SOURCES else "playstore", "context": None, "text": text}
    try:
        ex = s4_extract.extract(record, CODEBOOK)
    except BudgetExhausted:
        return 503, {"outcome": "unavailable", "message": "Today's free quota for the live demo is used up. "
                     "Please try again tomorrow; the results and evidence log tabs still work."}
    except LLMError:
        return 502, {"outcome": "unavailable", "message": "The model didn't respond properly just now. Please try again in a minute."}
    if ex.get("status") != "ok":
        return 200, {"outcome": "declined", "message": "The model's answer didn't fit the schema even after a retry, "
                     "so nothing is shown rather than a guess."}
    themes = [{**t, "name": THEMES.get(t["theme_id"], {}).get("name", "Other"),
               "question": THEMES.get(t["theme_id"], {}).get("question")} for t in ex["themes"]]
    verified = [t for t in themes if t["verified"]]
    return 200, {
        "outcome": "coded" if verified or ex["sip_status"] != "unclear" else "nothing_found",
        "sip_status": ex["sip_status"], "sip_status_evidence": ex.get("sip_status_evidence"),
        "sip_status_verified": ex.get("sip_status_verified"),
        "first_time_investor": ex["first_time_investor"], "first_time_evidence": ex.get("first_time_evidence"),
        "time_since_start": ex.get("time_since_start", "unclear"), "time_since_start_evidence": ex.get("time_since_start_evidence"),
        "themes": themes, "one_line_reason": ex.get("one_line_reason"),
        "quality": {"values_with_quotes": len(themes) + (ex["sip_status"] != "unclear"),
                    "unverified": sum(not t["verified"] for t in themes) + (not ex.get("sip_status_verified", True)),
                    "retried": ex.get("attempts", 1) > 1},
        "model": config.MODEL_EXTRACT, "disclaimer": DISCLAIMER,
    }


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):  # noqa: N802
        ip = (self.headers.get("x-forwarded-for") or self.client_address[0]).split(",")[0].strip()
        if rate_limited(ip):
            return self._send(429, {"outcome": "unavailable", "message": "That's the limit for now (10 tries an hour). Please come back later."})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("content-length") or 0)) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._send(400, {"outcome": "declined", "message": "Send JSON with a 'text' field."})
        code, out = run(body.get("text", ""), body.get("source", "playstore"))
        self._send(code, out)

    def do_GET(self):  # noqa: N802
        self._send(200, {"ok": True, "model": config.MODEL_EXTRACT, "provider": config.LLM_PROVIDER})
