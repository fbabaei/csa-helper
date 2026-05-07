"""Generate paste-ready Copilot Studio assets from agents/*.md.

Outputs:
  build/orchestrator.md            - instructions for the orchestrator agent
  build/agents/<name>.md           - instructions for each specialist agent
  build/combined-single-agent.md   - single-agent (Pattern A) inlined version
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
MANIFEST = REPO / "manifests" / "csa-helper-manifest.yaml"
DESC_FILE = ROOT / "agent-descriptions.yaml"
BUILD = ROOT / "build"


def main() -> None:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    descriptions = yaml.safe_load(DESC_FILE.read_text(encoding="utf-8")) or {}

    if BUILD.exists():
        shutil.rmtree(BUILD)
    (BUILD / "agents").mkdir(parents=True)

    orchestrator_id = "csa_orchestrator"
    specialists = []
    orchestrator_body = ""

    for entry in manifest["agents"]:
        agent_id: str = entry["id"]
        path = REPO / entry["file"]
        body = path.read_text(encoding="utf-8").strip()

        if agent_id == orchestrator_id:
            orchestrator_body = body
            continue

        out = BUILD / "agents" / f"{path.stem}.md"
        out.write_text(body + "\n", encoding="utf-8")
        specialists.append((agent_id, path.stem, body))

    # ---- orchestrator.md ----
    handoff_lines = []
    for agent_id, stem, _ in specialists:
        desc = (descriptions.get(agent_id) or "").strip()
        handoff_lines.append(f"- **{agent_id}** — {desc}")
    orch_out = (
        orchestrator_body
        + "\n\n---\n\n## Connected agents available\n\n"
        + "When a request matches one of the descriptions below, hand off to that "
        + "agent rather than answering directly.\n\n"
        + "\n".join(handoff_lines)
        + "\n"
    )
    (BUILD / "orchestrator.md").write_text(orch_out, encoding="utf-8")

    # ---- combined-single-agent.md ----
    combined = [orchestrator_body, "\n\n---\n\n## Specialist playbooks (inlined)\n"]
    for _, stem, body in specialists:
        combined.append(f"\n\n---\n\n# Playbook: {stem}\n\n{body}")
    (BUILD / "combined-single-agent.md").write_text("".join(combined) + "\n", encoding="utf-8")

    print(f"Wrote {len(specialists)} specialist files + orchestrator + combined to {BUILD}")


if __name__ == "__main__":
    main()
