"""Build the orchestrator + 10 specialists as a Microsoft Agent Framework team.

Each specialist is exposed to the orchestrator as a callable tool whose
description is read from copilot-studio/agent-descriptions.yaml. The
orchestrator decides which one(s) to invoke for each user prompt.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "manifests" / "csa-helper-manifest.yaml"
DESCRIPTIONS = REPO / "copilot-studio" / "agent-descriptions.yaml"

ORCHESTRATOR_ID = "csa_orchestrator"


@dataclass
class Specialist:
    id: str
    name: str
    description: str
    instructions: str


@dataclass
class Team:
    orchestrator_instructions: str
    specialists: list[Specialist]
    client: AzureOpenAI
    deployment: str

    def ask_specialist(self, specialist_id: str, request: str) -> str:
        spec = next(s for s in self.specialists if s.id == specialist_id)
        resp = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": spec.instructions},
                {"role": "user", "content": request},
            ],
        )
        return resp.choices[0].message.content or ""

    def ask(self, prompt: str) -> tuple[str, list[dict]]:
        """Ask the orchestrator. Returns (final_answer, trace)."""
        tools = [_tool_schema(s) for s in self.specialists]
        messages: list[dict] = [
            {"role": "system", "content": self.orchestrator_instructions},
            {"role": "user", "content": prompt},
        ]
        trace: list[dict] = []

        for _ in range(6):  # max 6 hand-offs
            resp = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                return (msg.content or "", trace)

            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                }
            )
            for tc in msg.tool_calls:
                spec_id = tc.function.name
                import json

                args = json.loads(tc.function.arguments or "{}")
                request = args.get("request", prompt)
                answer = self.ask_specialist(spec_id, request)
                trace.append({"agent": spec_id, "request": request, "answer": answer})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": answer,
                    }
                )
        return ("(reached max handoff depth)", trace)


def _tool_schema(s: Specialist) -> dict:
    return {
        "type": "function",
        "function": {
            "name": s.id,
            "description": s.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "The fully self-contained request to send to this specialist.",
                    }
                },
                "required": ["request"],
            },
        },
    }


def build_team() -> Team:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    descriptions = yaml.safe_load(DESCRIPTIONS.read_text(encoding="utf-8")) or {}

    orchestrator_instructions = ""
    specialists: list[Specialist] = []
    for entry in manifest["agents"]:
        body = (REPO / entry["file"]).read_text(encoding="utf-8").strip()
        if entry["id"] == ORCHESTRATOR_ID:
            orchestrator_instructions = body
            continue
        desc = (descriptions.get(entry["id"]) or "").strip()
        # H1 of the file as the human name.
        name = body.splitlines()[0].lstrip("# ").strip() or entry["id"]
        specialists.append(
            Specialist(id=entry["id"], name=name, description=desc, instructions=body)
        )

    if not orchestrator_instructions:
        raise RuntimeError(f"Orchestrator id '{ORCHESTRATOR_ID}' not found in manifest")

    endpoint = _require_env("AZURE_OPENAI_ENDPOINT")
    deployment = _require_env("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )
    return Team(
        orchestrator_instructions=orchestrator_instructions,
        specialists=specialists,
        client=client,
        deployment=deployment,
    )


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val
