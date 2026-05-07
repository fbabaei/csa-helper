"""LLM-as-judge eval for the local Agent Framework team.

Same approach as ../foundry/eval_runner.py but invokes the local team
instead of a Foundry-hosted orchestrator.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import AzureOpenAI

from build_team import build_team

REPO = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO / "eval"
RESULTS = Path(__file__).resolve().parent / "eval_results.json"

SCENARIO_RE = re.compile(
    r"## Scenario\s*\n(?P<scenario>.*?)\n## Expected behavior\s*\n(?P<expected>.*?)(?:\n## |\Z)",
    re.DOTALL,
)

JUDGE_SYSTEM = (
    "You are a strict but fair evaluator. Given a user prompt, an expected-behavior "
    "rubric, and an actual agent response, score the response against each criterion "
    "in the rubric. Reply ONLY in JSON with this shape: "
    '{"criteria":[{"criterion":"...","verdict":"PASS|FAIL","reason":"..."}],'
    '"overall":"PASS|FAIL","summary":"..."}'
)


def parse_case(path: Path) -> tuple[str, str] | None:
    text = path.read_text(encoding="utf-8")
    m = SCENARIO_RE.search(text)
    if not m:
        return None
    scenario = m.group("scenario").strip()
    scenario = re.sub(r"^\s*User asks:\s*", "", scenario, flags=re.IGNORECASE).strip()
    scenario = scenario.strip("\"' ")
    expected = m.group("expected").strip()
    return scenario, expected


def judge_client() -> tuple[AzureOpenAI, str]:
    endpoint = os.getenv("JUDGE_OPENAI_ENDPOINT") or os.environ["AZURE_OPENAI_ENDPOINT"]
    deployment = (
        os.getenv("JUDGE_MODEL_DEPLOYMENT_NAME") or os.environ["AZURE_OPENAI_DEPLOYMENT"]
    )
    api_version = os.getenv("JUDGE_OPENAI_API_VERSION", "2024-10-21")
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return (
        AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        ),
        deployment,
    )


def main() -> int:
    load_dotenv()
    team = build_team()
    judge, judge_deployment = judge_client()

    cases = sorted(EVAL_DIR.glob("[0-9][0-9]-*.md"))
    if not cases:
        print("no eval cases found", file=sys.stderr)
        return 2

    results = []
    for path in cases:
        parsed = parse_case(path)
        if not parsed:
            print(f"skip (unparseable): {path.name}")
            continue
        scenario, expected = parsed
        print(f"\n=== {path.name} ===")
        print(f"prompt: {scenario}")
        actual, trace = team.ask(scenario)

        verdict = judge.chat.completions.create(
            model=judge_deployment,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"USER PROMPT:\n{scenario}\n\n"
                        f"EXPECTED BEHAVIOR:\n{expected}\n\n"
                        f"ACTUAL RESPONSE:\n{actual}"
                    ),
                },
            ],
        )
        scoring = json.loads(verdict.choices[0].message.content or "{}")
        overall = scoring.get("overall", "FAIL")
        print(f"verdict: {overall}  -- {scoring.get('summary', '')}")
        results.append(
            {
                "case": path.name,
                "prompt": scenario,
                "actual": actual,
                "trace": [{"agent": h["agent"]} for h in trace],
                "scoring": scoring,
            }
        )

    RESULTS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    failed = [r for r in results if r["scoring"].get("overall") != "PASS"]
    print(f"\nWrote {RESULTS}. {len(results) - len(failed)}/{len(results)} passed.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
