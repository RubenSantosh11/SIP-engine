"""Stage 1: Apple App Store reviews of Groww (India storefront) via the public RSS feed -> data/raw/appstore.jsonl

The feed returns at most 10 pages x 50 of the most recent reviews.
"""
import argparse
import time

import requests

import config
from sip.common import log, make_record, save_source

FEED = "https://itunes.apple.com/{cc}/rss/customerreviews/page={page}/id={app}/sortby=mostrecent/json"


def main(limit: int) -> None:
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
        log.info("appstore page %d: %d entries", page, len(entries))
        if len(rows) >= limit:
            break
        time.sleep(config.POLITE_DELAY_SECONDS)
    save_source("appstore", rows[:limit])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin", action="store_true")
    a = ap.parse_args()
    main(config.THIN_SLICE_PER_SOURCE if a.thin else config.TARGET_PER_SOURCE["appstore"])
