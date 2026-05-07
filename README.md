# CSA Helper (Independent Agent Suite)

CSA Helper is an **independent, framework-agnostic, agent-based assistant system** designed to support
**Cloud & AI CSAs** delivering **AI Apps / Agents / Copilot / GenAI** solutions.

This repo focuses on:
- Production-ready delivery thinking
- Security-first behavior and safe information handling
- Outcome alignment (Job 1 / Job 2 discipline)
- Repeatable delivery guidance (VBD-style execution and milestones)

## What this is (and is not)
- ✅ A set of role-aligned **agent prompts** you can load into any runtime
- ✅ A standard set of **artifacts** (scope, RAID, security gate, recap, expansion plan)
- ❌ Not coupled to any specific agent platform or framework

## Repo layout
- `agents/` — one prompt per agent
- `manifests/` — lightweight manifest for the suite

## How to use

See **[QUICKSTART.md](QUICKSTART.md)** to pick a runtime and run it in ~5 minutes:
- [`agent-framework/`](agent-framework/) — local Python team via Azure OpenAI
- [`foundry/`](foundry/) — Azure AI Foundry connected agents
- [`copilot-studio/`](copilot-studio/) — paste-ready Copilot Studio instructions

All three load `agents/01-csa-orchestrator.md` as the entry point and route to specialists by intent.

## Notes
- These prompts include **hard guardrails** for safe handling of Microsoft/customer information.
- Where internal policies are required, the prompts instruct the agent to avoid inventing procedures and to require permission/owner context.
