"""Delete every agent created by register_agents.py."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

IDS_FILE = Path(__file__).resolve().parent / ".agent_ids.json"


def main() -> int:
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        print("ERROR: set PROJECT_ENDPOINT first.", file=sys.stderr)
        return 2
    if not IDS_FILE.exists():
        print("Nothing to clean up.")
        return 0

    ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())

    for agent_id in ids.get("all_ids", []):
        try:
            client.agents.delete_agent(agent_id)
            print(f"  - deleted {agent_id}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! failed to delete {agent_id}: {exc}", file=sys.stderr)

    IDS_FILE.unlink(missing_ok=True)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
