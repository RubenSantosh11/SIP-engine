"""Stage 1: TradingQ&A (public Discourse forum) posts via public JSON endpoints -> data/raw/tradingqna.jsonl

Uses /search.json to find SIP topics, then /t/{id}.json for the posts. One request per second.
"""
import argparse
import html
import re
import time

import requests

import config
from sip.common import log, make_record, read_jsonl, save_source

BASE = "https://tradingqna.com"


def _get(path: str, **params) -> dict:
    time.sleep(config.POLITE_DELAY_SECONDS)
    for attempt in range(4):
        resp = requests.get(BASE + path, params=params, headers={"User-Agent": config.HTTP_USER_AGENT}, timeout=30)
        if resp.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def html_to_text(cooked: str) -> str:
    cooked = re.sub(r"<aside class=\"quote.*?</aside>", " ", cooked, flags=re.S)  # drop quoted replies
    cooked = re.sub(r"<br\s*/?>|</p>|</li>", "\n", cooked)
    text = html.unescape(re.sub(r"<[^>]+>", " ", cooked))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def main(limit: int, queries: list[str], topics_per_query: int) -> None:
    have = len(read_jsonl(config.RAW_DIR / "tradingqna.jsonl"))
    topic_ids, rows = {}, []
    for q in queries:
        data = _get("/search.json", q=q)
        for t in data.get("topics", [])[:topics_per_query]:
            topic_ids.setdefault(t["id"], t["title"])
    log.info("tradingqna: %d candidate topics", len(topic_ids))
    for tid, title in topic_ids.items():
        if have + len(rows) >= limit:
            break
        topic = _get(f"/t/{tid}.json")
        for p in topic.get("post_stream", {}).get("posts", []):
            text = html_to_text(p.get("cooked", ""))
            if len(text) < 15:
                continue
            rows.append(make_record(
                "tradingqna", p["id"], (p.get("created_at") or "")[:10] or None, text,
                url=f"{BASE}/t/{topic.get('slug', '')}/{tid}/{p.get('post_number', 1)}", context=title,
                author=p.get("username"),
            ))
    save_source("tradingqna", rows[: max(0, limit - have)])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin", action="store_true")
    a = ap.parse_args()
    if a.thin:
        main(config.THIN_SLICE_PER_SOURCE["tradingqna"], config.TRADINGQNA_SEARCH_QUERIES[:3], 5)
    else:
        main(config.TARGET_PER_SOURCE["tradingqna"], config.TRADINGQNA_SEARCH_QUERIES, config.TRADINGQNA_MAX_TOPICS_PER_QUERY)
