"""Stage 1: Google Play reviews of the Groww app -> data/raw/playstore.jsonl"""
import argparse

from google_play_scraper import Sort, reviews

import config
from sip.common import make_record, save_source


def main(limit: int) -> None:
    rows, token = [], None
    while len(rows) < limit:
        batch, token = reviews(config.GROWW_PLAY_ID, lang="en", country="in", sort=Sort.NEWEST,
                               count=min(200, limit - len(rows)), continuation_token=token)
        if not batch:
            break
        for r in batch:
            rows.append(make_record(
                "playstore", r["reviewId"], r["at"].date().isoformat() if r.get("at") else None,
                r.get("content") or "", rating=r.get("score"),
                url=f"https://play.google.com/store/apps/details?id={config.GROWW_PLAY_ID}",
                author=r.get("userName"),
            ))
        if token is None:
            break
    save_source("playstore", rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin", action="store_true", help="thin-slice cap")
    a = ap.parse_args()
    main(config.THIN_SLICE_PER_SOURCE if a.thin else config.TARGET_PER_SOURCE["playstore"])
