"""
Register all CSA Helper agents in Microsoft Foundry.

The CSA Orchestrator is created last, with every other agent attached as a
ConnectedAgentTool so the orchestrator can dispatch to them via tool calls.

Outputs: .agent_ids.json (consumed by invoke.py and cleanup.py)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import yaml
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ConnectedAgentTool
from azure.identity import DefaultAzureCredential

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifests" / "csa-helper-manifest.yaml"
IDS_FILE = Path(__file__).resolve().parent / ".agent_ids.json"

ORCHESTRATOR_ID = "csa_orchestrator"


def _slug(name: str) -> str:
    """Foundry agent names accept letters, digits, _ and -."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", name)[:64]


def main() -> int:
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    model = os.environ.get("MODEL_DEPLOYMENT_NAME")
    if not endpoint or not model:
        print("ERROR: set PROJECT_ENDPOINT and MODEL_DEPLOYMENT_NAME first.", file=sys.stderr)
        return 2

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    agents_meta = manifest["agents"]
    project_name = manifest.get("name", "CSA Helper")

    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    agents = client.agents

    # --- Step 1: create every non-orchestrator agent first ---
    created: dict[str, dict] = {}  # id -> {agent_id, name, description, instructions}
    for entry in agents_meta:
        local_id = entry["id"]
        if local_id == ORCHESTRATOR_ID:
            continue

        body = (ROOT / entry["file"]).read_text(encoding="utf-8")
        first_line = next((ln for ln in body.splitlines() if ln.strip()), local_id)
        display = first_line.lstrip("# ").strip() or local_id
        name = _slug(f"{project_name}-{local_id}")

        print(f"  + creating {name} ...")
        agent = agents.create_agent(
            model=model,
            name=name,
            description=display,
            instructions=body,
        )
        created[local_id] = {
            "agent_id": agent.id,
            "name": name,
            "description": display,
        }

    # --- Step 2: build ConnectedAgentTool list and create the orchestrator ---
    connected_tools: list[ConnectedAgentTool] = []
    for local_id, meta in created.items():
        connected_tools.append(
            ConnectedAgentTool(
                id=meta["agent_id"],
                name=local_id,           # the orchestrator references this name
                description=meta["description"],
            )
        )

    orch_entry = next(e for e in agents_meta if e["id"] == ORCHESTRATOR_ID)
    orch_body = (ROOT / orch_entry["file"]).read_text(encoding="utf-8")
    orch_name = _slug(f"{project_name}-{ORCHESTRATOR_ID}")

    print(f"  + creating orchestrator {orch_name} with {len(connected_tools)} connected agents ...")
    orchestrator = agents.create_agent(
        model=model,
        name=orch_name,
        description="CSA Helper orchestrator (Job 1 / Job 2 router)",
        instructions=orch_body,
        tools=[t.definitions[0] for t in connected_tools],
    )

    all_ids = [meta["agent_id"] for meta in created.values()] + [orchestrator.id]
    IDS_FILE.write_text(
        json.dumps(
            {
                "orchestrator_id": orchestrator.id,
                "orchestrator_name": orch_name,
                "all_ids": all_ids,
                "connected": {k: v["agent_id"] for k, v in created.items()},
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(f"Done. Orchestrator id: {orchestrator.id}")
    print(f"Wrote {IDS_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
