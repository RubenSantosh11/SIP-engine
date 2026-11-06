"""Stage 1: YouTube comments on SIP-related videos -> data/raw/youtube.jsonl

Quota: search.list costs 100 units, so each query is searched ONCE and the video IDs are
stored in data/raw/youtube_videos.json. Comment pages (1 unit each) are then paged from that list.
"""
import argparse
import datetime as dt
import json

import requests

import config
from sip.common import get_secret, log, make_record, save_source

API = "https://www.googleapis.com/youtube/v3/"
VIDEOS_FILE = config.RAW_DIR / "youtube_videos.json"
UNITS_FILE = config.STATE_DIR / "youtube_units.json"


def _units_today() -> int:
    d = json.loads(UNITS_FILE.read_text()) if UNITS_FILE.exists() else {}
    return d.get(dt.date.today().isoformat(), 0)


def _spend(units: int) -> None:
    d = json.loads(UNITS_FILE.read_text()) if UNITS_FILE.exists() else {}
    today = dt.date.today().isoformat()
    if d.get(today, 0) + units > config.YOUTUBE_DAILY_UNIT_BUDGET:
        raise SystemExit(f"YouTube unit budget ({config.YOUTUBE_DAILY_UNIT_BUDGET}/day) reached; re-run tomorrow")
    d[today] = d.get(today, 0) + units
    UNITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    UNITS_FILE.write_text(json.dumps(d))


def _get(endpoint: str, cost: int, **params) -> dict:
    _spend(cost)
    resp = requests.get(API + endpoint, params={**params, "key": get_secret("YOUTUBE_API_KEY")}, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"YouTube {endpoint} HTTP {resp.status_code}: {resp.json().get('error', {}).get('message', '')[:200]}")
    return resp.json()


def search_videos(queries: list[str], per_query: int) -> dict:
    videos = json.loads(VIDEOS_FILE.read_text()) if VIDEOS_FILE.exists() else {"queries_done": [], "videos": {}}
    for q in queries:
        if q in videos["queries_done"]:
            continue
        data = _get("search", 100, part="snippet", q=q, type="video", maxResults=per_query,
                    regionCode="IN", relevanceLanguage="en")
        for item in data.get("items", []):
            vid = item["id"]["videoId"]
            videos["videos"].setdefault(vid, {"title": item["snippet"]["title"], "query": q, "pages_done": 0, "next": None, "finished": False})
        videos["queries_done"].append(q)
        VIDEOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        VIDEOS_FILE.write_text(json.dumps(videos, indent=1))
        log.info("youtube search %r -> %d videos", q, len(data.get("items", [])))
    return videos


def main(limit: int, queries: list[str], per_query: int) -> None:
    """Spread comments evenly: each video gets at most limit / n_videos top comments (by relevance)."""
    videos = search_videos(queries, per_query)
    per_video = -(-limit // max(1, len(videos["videos"])))
    rows = []
    for vid, v in videos["videos"].items():
        v.setdefault("n", 0)
        while not v["finished"] and v["n"] < per_video:
            params = dict(part="snippet", videoId=vid, maxResults=min(100, per_video - v["n"]),
                          order="relevance", textFormat="plainText")
            if v["next"]:
                params["pageToken"] = v["next"]
            try:
                data = _get("commentThreads", 1, **params)
            except RuntimeError as e:  # comments disabled, etc.
                log.warning("skip %s: %s", vid, e)
                v["finished"] = True
                break
            for item in data.get("items", []):
                s = item["snippet"]["topLevelComment"]["snippet"]
                rows.append(make_record(
                    "youtube", item["id"], s.get("publishedAt", "")[:10] or None, s.get("textOriginal") or s.get("textDisplay", ""),
                    url=f"https://www.youtube.com/watch?v={vid}", context=v["title"],
                    author=s.get("authorChannelId", {}).get("value") or s.get("authorDisplayName"),
                ))
            v["n"] += len(data.get("items", []))
            v["pages_done"] += 1
            v["next"] = data.get("nextPageToken")
            v["finished"] = v["next"] is None or not data.get("items")
        VIDEOS_FILE.write_text(json.dumps(videos, indent=1))
    save_source("youtube", rows)
    log.info("youtube: %d videos, cap %d comments each; units used today: %d", len(videos["videos"]), per_video, _units_today())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thin", action="store_true")
    a = ap.parse_args()
    if a.thin:
        main(config.THIN_SLICE_PER_SOURCE["youtube"], config.YOUTUBE_SEARCH_QUERIES[:1], 5)
    else:
        main(config.TARGET_PER_SOURCE["youtube"], config.YOUTUBE_SEARCH_QUERIES, config.YOUTUBE_VIDEOS_PER_QUERY)
