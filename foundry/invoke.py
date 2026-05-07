"""
Send a single prompt to the registered CSA Orchestrator and print the reply.

Usage:
    python invoke.py "Help me scope a 6-week AI pilot for a retail customer."
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder, MessageRole
from azure.identity import DefaultAzureCredential

IDS_FILE = Path(__file__).resolve().parent / ".agent_ids.json"


def main() -> int:
    if len(sys.argv) < 2:
        print('Usage: python invoke.py "<your question>"', file=sys.stderr)
        return 2

    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        print("ERROR: set PROJECT_ENDPOINT first.", file=sys.stderr)
        return 2
    if not IDS_FILE.exists():
        print(f"ERROR: {IDS_FILE} not found. Run register_agents.py first.", file=sys.stderr)
        return 2

    ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))
    orchestrator_id = ids["orchestrator_id"]
    user_prompt = sys.argv[1]

    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    agents = client.agents

    thread = agents.threads.create()
    agents.messages.create(thread_id=thread.id, role="user", content=user_prompt)

    print(f"-> asking orchestrator {orchestrator_id} ...")
    run = agents.runs.create_and_process(thread_id=thread.id, agent_id=orchestrator_id)
    if run.status == "failed":
        print(f"Run failed: {run.last_error}", file=sys.stderr)
        return 1

    messages = agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    print()
    for m in messages:
        if m.role == MessageRole.AGENT and m.text_messages:
            print(m.text_messages[-1].text.value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
