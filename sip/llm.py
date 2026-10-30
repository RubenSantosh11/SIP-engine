"""The single LLM entry point (llm_call) plus request budget and on-disk cache.

Swap providers by changing _gemini_generate only; callers never see provider details.
"""
import datetime as dt
import json
import time

import requests

import config
from sip.common import get_secret, log, sha


class BudgetExhausted(Exception):
    """The local daily request budget, or the provider's quota/credits, is used up. Stop and resume later."""


class LLMError(Exception):
    pass


_last_call_at = 0.0


def _usage_path():
    return config.STATE_DIR / "llm_usage.json"


def _load_usage() -> dict:
    p = _usage_path()
    return json.loads(p.read_text()) if p.exists() else {}


def _bump_usage(model: str) -> None:
    usage = _load_usage()
    today = dt.date.today().isoformat()
    usage.setdefault(today, {}).setdefault(model, 0)
    usage[today][model] += 1
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    _usage_path().write_text(json.dumps(usage, indent=1))


def requests_used_today(model: str) -> int:
    return _load_usage().get(dt.date.today().isoformat(), {}).get(model, 0)


def _check_budget(model: str) -> None:
    budget = config.DAILY_REQUEST_BUDGET.get(model, 0)
    if requests_used_today(model) >= budget:
        raise BudgetExhausted(f"daily request budget for {model} reached ({budget}); re-run tomorrow to resume")


def _is_hard_quota(message: str) -> bool:
    """Quota errors that retrying will not fix (daily cap, depleted credits)."""
    m = message.lower()
    return any(s in m for s in ("per day", "perday", "credits are depleted", "billing", "limit: 0"))


def _gemini_generate(model: str, prompt: str, system: str | None) -> str:
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": config.TEMPERATURE, "responseMimeType": "application/json"},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}
    resp = requests.post(
        config.GEMINI_ENDPOINT.format(model=model),
        headers={"x-goog-api-key": get_secret("GEMINI_API_KEY"), "Content-Type": "application/json"},
        json=body,
        timeout=config.REQUEST_TIMEOUT_SECONDS,
    )
    if resp.status_code != 200:
        try:
            msg = resp.json().get("error", {}).get("message", "")
        except ValueError:
            msg = resp.text[:300]
        raise LLMError(f"HTTP {resp.status_code}: {msg}")
    data = resp.json()
    try:
        return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError):
        raise LLMError(f"no text in response (finishReason={data.get('candidates', [{}])[0].get('finishReason')})")


def llm_call(model: str, prompt: str, system: str | None = None) -> dict | list:
    """Call the model once (with retries) and return parsed JSON. Counts every HTTP request against the budget."""
    global _last_call_at
    for attempt in range(config.MAX_RETRIES + 1):
        _check_budget(model)
        wait = config.MIN_SECONDS_BETWEEN_CALLS - (time.time() - _last_call_at)
        if wait > 0:
            time.sleep(wait)
        _last_call_at = time.time()
        _bump_usage(model)
        try:
            text = _gemini_generate(model, prompt, system)
            return json.loads(text)
        except json.JSONDecodeError as e:
            err = f"malformed JSON: {e}"
            retryable = True
        except requests.RequestException as e:
            err, retryable = f"network: {type(e).__name__}", True
        except LLMError as e:
            err = str(e)
            if err.startswith("HTTP 429") and _is_hard_quota(err):
                raise BudgetExhausted(f"provider quota exhausted: {err[:200]}")
            retryable = err.startswith(("HTTP 429", "HTTP 5")) or "no text" in err
        if not retryable or attempt == config.MAX_RETRIES:
            raise LLMError(err)
        delay = config.BACKOFF_BASE_SECONDS * 2 ** attempt
        log.warning("LLM call failed (%s); retry %d in %.0fs", err[:120], attempt + 1, delay)
        time.sleep(delay)
    raise LLMError("unreachable")


# ---- Disk cache: one JSON file per (stage, record_id, prompt version) ----

def cache_path(stage: str, record_id: str, version: str):
    return config.CACHE_DIR / stage / f"{record_id}__{version}.json"


def cache_get(stage: str, record_id: str, version: str):
    p = cache_path(stage, record_id, version)
    return json.loads(p.read_text()) if p.exists() else None


def cache_put(stage: str, record_id: str, version: str, value) -> None:
    p = cache_path(stage, record_id, version)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=1))
