"""Stage 1: public Discourse forums via their public JSON endpoints -> data/raw/<forum>.jsonl

- TradingQ&A: /search.json for SIP queries (search is allowed by its robots.txt).
- ValuePickr: its robots.txt disallows /search, so we list topics in chosen categories
  (/c/<slug>/<id>.json) and keep topics whose titles mention SIPs / mutual funds.
Then /t/<id>.json (plus a few pages) for the posts. One request per second.
"""
import argparse
import html
import re
import time

import requests

import config
from sip.common import log, make_record, read_jsonl, save_source

FORUMS = {"tradingqna": "https://tradingqna.com", "valuepickr": "https://forum.valuepickr.com"}


def _get(base: str, path: str, **params) -> dict | None:
    time.sleep(config.POLITE_DELAY_SECONDS)
    for attempt in range(4):
        resp = requests.get(base + path, params=params, headers={"User-Agent": config.HTTP_USER_AGENT}, timeout=30)
        if resp.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def html_to_text(cooked: str) -> str:
    cooked = re.sub(r"<aside class=\"quote.*?</aside>", " ", cooked, flags=re.S)  # drop quoted replies
    cooked = re.sub(r"<br\s*/?>|</p>|</li>", "\n", cooked)
    text = html.unescape(re.sub(r"<[^>]+>", " ", cooked))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


def tradingqna_topics(base: str, queries: list[str], per_query: int) -> dict:
    topics = {}
    for q in queries:
        for t in (_get(base, "/search.json", q=q) or {}).get("topics", [])[:per_query]:
            topics.setdefault(t["id"], t["title"])
    return topics


def valuepickr_topics(base: str) -> dict:
    title_re = re.compile(config.VALUEPICKR_TITLE_TERMS, re.I)
    topics = {}
    for cid, slug in config.VALUEPICKR_CATEGORIES.items():
        page = 0
        while True:
            data = _get(base, f"/c/{slug}/{cid}.json", page=page)
            batch = (data or {}).get("topic_list", {}).get("topics", [])
            if not batch:
                break
            for t in batch:
                if title_re.search(t["title"]):
                    topics.setdefault(t["id"], t["title"])
            page += 1
    return topics


def topic_posts(forum: str, base: str, tid: int, title: str, max_pages: int) -> list[dict]:
    rows = []
    for page in range(1, max_pages + 1):
        topic = _get(base, f"/t/{tid}.json", page=page)
        posts = (topic or {}).get("post_stream", {}).get("posts", [])
        if not posts:
            break
        for p in posts:
            text = html_to_text(p.get("cooked", ""))
            if len(text) >= 15:
                rows.append(make_record(
                    forum, p["id"], (p.get("created_at") or "")[:10] or None, text,
                    url=f"{base}/t/{topic.get('slug', '')}/{tid}/{p.get('post_number', 1)}", context=title,
                    author=p.get("username"),
                ))
    return rows


def main(forum: str, thin: bool) -> None:
    base = FORUMS[forum]
    limit = config.THIN_SLICE_PER_SOURCE.get(forum, 30) if thin else config.FORUM_TARGET[forum]
    have = len(read_jsonl(config.RAW_DIR / f"{forum}.jsonl"))
    if forum == "tradingqna":
        queries = config.TRADINGQNA_SEARCH_QUERIES[:3] if thin else config.TRADINGQNA_SEARCH_QUERIES
        topics = tradingqna_topics(base, queries, 5 if thin else config.TRADINGQNA_MAX_TOPICS_PER_QUERY)
        max_pages = 1
    else:
        topics = valuepickr_topics(base)
        max_pages = config.VALUEPICKR_MAX_PAGES_PER_TOPIC
    log.info("%s: %d candidate topics", forum, len(topics))
    rows = []
    for tid, title in topics.items():
        if have + len(rows) >= limit:
            break
        rows += topic_posts(forum, base, tid, title, max_pages)
    save_source(forum, rows[: max(0, limit - have)])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("forum", choices=list(FORUMS))
    ap.add_argument("--thin", action="store_true")
    a = ap.parse_args()
    main(a.forum, a.thin)
