# CSA Helper on Microsoft Agent Framework

Run the same orchestrator + 10 specialists locally (or in any container host)
using the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
Python SDK.

This is the **code-first** option — no Foundry project, no Copilot Studio
tenant required. You bring an Azure OpenAI (or OpenAI) endpoint and run it.

| File | Purpose |
|---|---|
| `requirements.txt` | `openai`, `azure-identity`, `pyyaml`, `python-dotenv`. |
| `build_team.py` | Reads `manifests/csa-helper-manifest.yaml` and `agents/*.md`, returns the orchestrator wired to all specialists as handoff tools. Importable. |
| `chat.py` | Interactive REPL — type a prompt, see the routed answer. |
| `run_once.py` | One-shot runner: `python run_once.py "your prompt"` → prints the answer + the routing trace. |
| `eval_runner.py` | Same LLM-as-judge harness as the Foundry example, but pointed at the local agent team. |
| `.env.example` | Required env vars. |

> Built on the Azure OpenAI tool-calling primitive that Microsoft Agent Framework
> itself uses under the hood — minimal dependencies, swap in `agent-framework`
> SDK later if you want richer plumbing (group chat, observability, etc).

---

## Setup

```powershell
cd C:\Users\fbabaei\workspace\csa-helper\agent-framework
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
notepad .env   # fill in AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_DEPLOYMENT
```

Auth uses `DefaultAzureCredential` (so `az login` is enough). The identity
needs **Cognitive Services OpenAI User** on the Azure OpenAI resource.

---

## Run it

```powershell
# Interactive
python chat.py

# Single prompt
python run_once.py "Customer wants to commit a Foundry POC milestone next week — what's the plan?"

# Score against eval/*.md
python eval_runner.py
```

`chat.py` shows the routing trace (which specialist the orchestrator hands off
to) inline so you can see the multi-agent behavior.

---

## How it's wired

```
                  ┌──────────────────────┐
   user prompt ──▶│   csa_orchestrator   │── ChatAgent (gpt-4o)
                  └─────────┬────────────┘
                            │  handoff tools
        ┌──────────┬────────┼────────┬───────────┬─ ... ──┐
        ▼          ▼        ▼        ▼           ▼        ▼
  security    intake     milestone  vbd      ai-apps    impact
  sentinel              coach      planner   architect  reporting
```

Each specialist is a `ChatAgent` whose system prompt is the matching file in
`agents/`. They are exposed to the orchestrator as **callable tools** with the
agent's name + one-line description from
[`../copilot-studio/agent-descriptions.yaml`](../copilot-studio/agent-descriptions.yaml)
— same source of truth used by the Copilot Studio router.

---

## Compared to the other runtimes

| Aspect | This (Agent Framework) | Foundry (`../foundry`) | Copilot Studio (`../copilot-studio`) |
|---|---|---|---|
| Where it runs | Your laptop / any container host | Microsoft Foundry project | Copilot Studio (M365) |
| Auth | `DefaultAzureCredential` → AOAI | `DefaultAzureCredential` → Foundry | M365 SSO |
| State | In-process | Foundry threads | Copilot Studio sessions |
| Best for | Iteration, eval, embedding in apps | Hosted agents, observability | Business users, Teams/M365 channel |

All three read from the **same** `agents/*.md` and manifest, so a change to a
playbook propagates everywhere after a re-import / redeploy.
