"""Shared helpers: secrets, JSONL I/O, hashing, logging."""
import hashlib
import json
import logging
import os
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sip")


def get_secret(name: str) -> str:
    """Read a key from the environment, falling back to a local .env. Never log the value."""
    value = os.environ.get(name)
    if not value:
        try:
            from dotenv import load_dotenv
            load_dotenv(Path(__file__).parent.parent / ".env")
            value = os.environ.get(name)
        except ImportError:
            pass
    if not value:
        raise RuntimeError(f"{name} is not set (environment variable or .env)")
    return value


def sha(text: str, n: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def author_hash(name: str | None) -> str | None:
    """One-way hash so no username or profile info is stored."""
    return sha("author:" + name, 12) if name else None


def make_record(source: str, native_id: str, date: str | None, text: str,
                rating=None, url=None, context=None, author=None) -> dict:
    return {
        "record_id": f"{source}_{sha(source + ':' + str(native_id), 12)}",
        "source": source,
        "date": date,
        "rating": rating,
        "text": text.strip(),
        "url": url,
        "context": context,  # e.g. YouTube video title or forum topic title
        "author_hash": author_hash(author),
    }


def normalise(text: str) -> str:
    """Whitespace + case normalisation only (used for dedup and evidence-span checks)."""
    return re.sub(r"\s+", " ", text or "").strip().lower()


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def dedupe(rows: list[dict]) -> list[dict]:
    """Drop repeated record_ids and repeated (source, normalised text) pairs."""
    seen_ids, seen_text, out = set(), set(), []
    for r in rows:
        key = (r["source"], normalise(r["text"]))
        if r["record_id"] in seen_ids or key in seen_text or not r["text"]:
            continue
        seen_ids.add(r["record_id"])
        seen_text.add(key)
        out.append(r)
    return out


def save_source(source: str, rows: list[dict]) -> list[dict]:
    """Merge new rows with any already collected for this source, dedupe, write, log the count."""
    import config
    path = config.RAW_DIR / f"{source}.jsonl"
    before = read_jsonl(path)
    merged = dedupe(before + rows)
    write_jsonl(path, merged)
    log.info("%s: %d fetched, %d total after dedupe (was %d)", source, len(rows), len(merged), len(before))
    return merged
