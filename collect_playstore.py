"""Stage 1: Google Play reviews of Groww and other Indian investing apps -> data/raw/playstore.jsonl"""
import argparse

from google_play_scraper import Sort, reviews

import config
from sip.common import log, make_record, save_source


def fetch_app(name: str, app_id: str, limit: int) -> list[dict]:
    rows, token = [], None
    while len(rows) < limit:
        batch, token = reviews(app_id, lang="en", country="in", sort=Sort.NEWEST,
                               count=min(200, limit - len(rows)), continuation_token=token)
        if not batch:
            break
        for r in batch:
            rows.append(make_record(
                "playstore", r["reviewId"], r["at"].date().isoformat() if r.get("at") else None,
                r.get("content") or "", rating=r.get("score"),
                url=f"https://play.google.com/store/apps/details?id={app_id}",
                author=r.get("userName"), app=name,
            ))
        if token is None:
            break
    log.info("playstore %s: %d reviews", name, len(rows))
    return rows[:limit]


def main(thin: bool) -> None:
    rows = []
    for name, app_id in config.PLAY_APPS.items():
        if thin and name != "groww":
            continue
        limit = config.THIN_SLICE_PER_SOURCE["playstore"] if thin else \
            config.PLAY_REVIEWS_PER_APP.get(name, config.PLAY_REVIEWS_DEFAULT)
        rows += fetch_app(name, app_id, limit)
    save_source("playstore", rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin", action="store_true", help="thin-slice cap (Groww only)")
    main(ap.parse_args().thin)
