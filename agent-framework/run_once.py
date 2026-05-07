"""One-shot runner: python run_once.py "your prompt here"."""
from __future__ import annotations

import json
import sys

from dotenv import load_dotenv

from build_team import build_team


def main() -> int:
    if len(sys.argv) < 2:
        print('usage: python run_once.py "your prompt here"', file=sys.stderr)
        return 2
    load_dotenv()
    team = build_team()
    answer, trace = team.ask(" ".join(sys.argv[1:]))
    print("=== trace ===")
    print(json.dumps([{"agent": h["agent"], "request": h["request"]} for h in trace], indent=2))
    print("\n=== answer ===")
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
