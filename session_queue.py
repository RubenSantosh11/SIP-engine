"""Helper for the "session" LLM provider (Claude answering inside a Claude Code session).

  python session_queue.py status                 # count pending requests per stage
  python session_queue.py show [prefix] [--n N]  # print pending prompts (data section only after the first)
  python session_queue.py answer FILE.jsonl      # FILE lines: {"key": ..., "answer": <JSON>}

Answers are written to data/session/answers/<key>.json; re-run the stage script to ingest them.
"""
import json
import sys
from collections import Counter

import config

REQ, ANS = config.SESSION_DIR / "requests", config.SESSION_DIR / "answers"


def pending(prefix: str = ""):
    if not REQ.exists():
        return []
    return sorted(p for p in REQ.glob(f"{prefix}*.json") if not (ANS / p.name).exists())


def main(argv):
    cmd = argv[0] if argv else "status"
    if cmd == "status":
        c = Counter(p.name.split("__")[0] for p in pending())
        print(dict(c) or "nothing pending")
    elif cmd == "show":
        prefix = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else ""
        n = int(argv[argv.index("--n") + 1]) if "--n" in argv else 10**9
        for i, p in enumerate(pending(prefix)[:n]):
            req = json.loads(p.read_text())
            print(f"===== KEY {req['key']}")
            print(req["prompt"] if i == 0 else req["prompt"].split("\n\n", 1)[-1] if "ITEMS:" not in req["prompt"]
                  else req["prompt"].split("ITEMS:", 1)[1])
    elif cmd == "answer":
        ANS.mkdir(parents=True, exist_ok=True)
        n = 0
        for line in open(argv[1], encoding="utf-8"):
            if line.strip():
                row = json.loads(line)
                (ANS / f"{row['key']}.json").write_text(json.dumps(row["answer"], ensure_ascii=False, indent=1))
                n += 1
        print(f"wrote {n} answers")


if __name__ == "__main__":
    main(sys.argv[1:])
