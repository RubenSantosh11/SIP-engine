"""Stage 1: Apple App Store reviews of Groww (India storefront) -> data/raw/appstore.jsonl

Two public, login-free routes:
1. The legacy RSS feed (up to 500 recent reviews). As of Oct 2026 it returns no entries for Groww.
2. The public app page's server-rendered data, which embeds only about 10 reviews.
Apple's review API needs a bearer token pulled from the site's JavaScript; we do NOT use it.
"""
import argparse
import json
import re
import time

import requests

import config
from sip.common import dedupe, log, make_record, save_source

FEED = "https://itunes.apple.com/{cc}/rss/customerreviews/page={page}/id={app}/sortby=mostrecent/json"
PAGE = "https://apps.apple.com/{cc}/app/id{app}?see-all=reviews"


def from_rss(limit: int) -> list[dict]:
    rows = []
    for page in range(1, 11):
        resp = requests.get(FEED.format(cc=config.APPSTORE_COUNTRY, page=page, app=config.GROWW_APPSTORE_ID),
                            headers={"User-Agent": config.HTTP_USER_AGENT}, timeout=30)
        resp.raise_for_status()
        entries = resp.json().get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        entries = [e for e in entries if "im:rating" in e]  # skip the app-info entry
        if not entries:
            break
        for e in entries:
            title = e.get("title", {}).get("label", "")
            body = e.get("content", {}).get("label", "")
            rows.append(make_record(
                "appstore", e["id"]["label"], e.get("updated", {}).get("label", "")[:10] or None,
                f"{title}\n{body}" if title else body, rating=int(e["im:rating"]["label"]),
                url=f"https://apps.apple.com/{config.APPSTORE_COUNTRY}/app/id{config.GROWW_APPSTORE_ID}",
                author=e.get("author", {}).get("name", {}).get("label"),
            ))
        if len(rows) >= limit:
            break
        time.sleep(config.POLITE_DELAY_SECONDS)
    log.info("appstore RSS: %d reviews", len(rows))
    return rows


def from_page() -> list[dict]:
    resp = requests.get(PAGE.format(cc=config.APPSTORE_COUNTRY, app=config.GROWW_APPSTORE_ID),
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    m = re.search(r'id="serialized-server-data">(.*?)</script>', resp.text, re.S)
    if not m:
        return []
    found = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("$kind") == "Review":
                found.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(json.loads(m.group(1)))
    rows = []
    for r in found:
        title, body = r.get("title") or "", r.get("contents") or ""
        rows.append(make_record(
            "appstore", r["id"], (r.get("date") or "")[:10] or None,
            f"{title}\n{body}" if title else body, rating=r.get("rating"),
            url=f"https://apps.apple.com/{config.APPSTORE_COUNTRY}/app/id{config.GROWW_APPSTORE_ID}",
            author=r.get("reviewerName"),
        ))
    log.info("appstore page: %d reviews", len(rows))
    return rows


def main(limit: int) -> None:
    rows = from_rss(limit) or from_page()
    save_source("appstore", dedupe(rows)[:limit])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin", action="store_true")
    a = ap.parse_args()
    main(config.THIN_SLICE_PER_SOURCE["appstore"] if a.thin else config.TARGET_PER_SOURCE["appstore"])
