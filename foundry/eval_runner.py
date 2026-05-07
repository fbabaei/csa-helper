"""
Run the four eval/*.md scenarios against the registered CSA Orchestrator,
score each one with an LLM judge, and write results to eval_results.json.

Usage:
    python eval_runner.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder, MessageRole
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "eval"
IDS_FILE = Path(__file__).resolve().parent / ".agent_ids.json"
RESULTS_FILE = Path(__file__).resolve().parent / "eval_results.json"

JUDGE_SYSTEM = """You are an evaluation judge for an AI agent system.
You will be given:
1) A scenario (user prompt sent to the agent)
2) The expected behavior (criteria the response must meet)
3) The agent's actual response

Score each criterion as PASS or FAIL, then give an overall verdict.

Reply ONLY with valid JSON of the form:
{
  "criteria": [
    {"criterion": "<short description>", "verdict": "PASS|FAIL", "reason": "<one sentence>"}
  ],
  "overall": "PASS|FAIL",
  "summary": "<one sentence>"
}
"""


def parse_scenario(md_text: str) -> tuple[str, str]:
    """Extract the user prompt and the expected-behavior block from an eval file."""
    scenario_match = re.search(
        r"##\s*Scenario\s*\n(?:User asks:\s*\n)?\"?(.+?)\"?\s*\n##\s*Expected behavior",
        md_text,
        re.DOTALL,
    )
    expected_match = re.search(
        r"##\s*Expected behavior\s*\n(.+?)$",
        md_text,
        re.DOTALL,
    )
    user_prompt = (scenario_match.group(1).strip() if scenario_match else "").strip().strip('"')
    expected = expected_match.group(1).strip() if expected_match else ""
    return user_prompt, expected


def ask_orchestrator(client: AIProjectClient, orchestrator_id: str, prompt: str) -> str:
    agents = client.agents
    thread = agents.threads.create()
    agents.messages.create(thread_id=thread.id, role="user", content=prompt)
    run = agents.runs.create_and_process(thread_id=thread.id, agent_id=orchestrator_id)
    if run.status == "failed":
        return f"[run failed: {run.last_error}]"
    msgs = agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    parts: list[str] = []
    for m in msgs:
        if m.role == MessageRole.AGENT and m.text_messages:
            parts.append(m.text_messages[-1].text.value)
    return "\n\n".join(parts).strip()


def judge(judge_client: AzureOpenAI, judge_model: str, scenario: str, expected: str, actual: str) -> dict:
    user_msg = (
        f"## Scenario (user prompt)\n{scenario}\n\n"
        f"## Expected behavior\n{expected}\n\n"
        f"## Actual response\n{actual}\n"
    )
    resp = judge_client.chat.completions.create(
        model=judge_model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)


def main() -> int:
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    judge_endpoint = os.environ.get("JUDGE_OPENAI_ENDPOINT")
    judge_model = os.environ.get("JUDGE_MODEL_DEPLOYMENT_NAME") or os.environ.get("MODEL_DEPLOYMENT_NAME")
    api_version = os.environ.get("JUDGE_OPENAI_API_VERSION", "2024-10-21")

    if not endpoint or not judge_endpoint or not judge_model:
        print(
            "ERROR: set PROJECT_ENDPOINT, JUDGE_OPENAI_ENDPOINT, JUDGE_MODEL_DEPLOYMENT_NAME first.",
            file=sys.stderr,
        )
        return 2
    if not IDS_FILE.exists():
        print(f"ERROR: {IDS_FILE} not found. Run register_agents.py first.", file=sys.stderr)
        return 2

    ids = json.loads(IDS_FILE.read_text(encoding="utf-8"))
    orchestrator_id = ids["orchestrator_id"]

    project_client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    credential = DefaultAzureCredential()
    judge_client = AzureOpenAI(
        azure_endpoint=judge_endpoint,
        api_version=api_version,
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
    )

    cases = sorted(EVAL_DIR.glob("[0-9][0-9]-*.md"))
    if not cases:
        print(f"No eval cases found under {EVAL_DIR}", file=sys.stderr)
        return 1

    results: list[dict] = []
    pass_count = 0
    for path in cases:
        text = path.read_text(encoding="utf-8")
        prompt, expected = parse_scenario(text)
        if not prompt:
            print(f"  ! skipping {path.name} (couldn't parse Scenario block)")
            continue

        print(f"  > {path.name}")
        print(f"      asking orchestrator ...")
        t0 = time.time()
        actual = ask_orchestrator(project_client, orchestrator_id, prompt)
        run_s = round(time.time() - t0, 1)

        print(f"      judging ({run_s}s run) ...")
        verdict = judge(judge_client, judge_model, prompt, expected, actual)

        if verdict.get("overall") == "PASS":
            pass_count += 1
            print(f"      PASS - {verdict.get('summary', '')}")
        else:
            print(f"      FAIL - {verdict.get('summary', '')}")

        results.append(
            {
                "case": path.name,
                "prompt": prompt,
                "expected": expected,
                "actual": actual,
                "judge": verdict,
                "run_seconds": run_s,
            }
        )

    summary = {
        "total": len(results),
        "passed": pass_count,
        "failed": len(results) - pass_count,
        "results": results,
    }
    RESULTS_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print()
    print(f"Result: {pass_count}/{len(results)} passed. Wrote {RESULTS_FILE}")
    return 0 if pass_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
