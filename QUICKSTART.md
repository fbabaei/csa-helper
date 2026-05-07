# Quick Start — CSA Helper

Pick **one** of three runtimes. All three load the same agent prompts in [`agents/`](agents/) and the same manifest in [`manifests/csa-helper-manifest.yaml`](manifests/csa-helper-manifest.yaml).

| Runtime | Best for | Setup time | Hosted? |
|---|---|---|---|
| [`agent-framework/`](agent-framework/) | Local dev, scripting, CI evals, REST hosting | ~5 min | Local Python (or container via [AAF](https://github.com/fbabaei_microsoft/azure-architecture-factory)) |
| [`foundry/`](foundry/) | Azure-managed agents, traceability in Foundry portal | ~10 min | Azure AI Foundry |
| [`copilot-studio/`](copilot-studio/) | Business users, M365 chat surfaces, Teams | ~15 min | Microsoft Copilot Studio |

Prereqs for all: `git clone https://github.com/fbabaei/csa-helper && cd csa-helper`, Python 3.10+, `az login`.

---

## Option 1 — `agent-framework/` (local Python team)

Runs the orchestrator + 9 specialists as a tool-calling loop against Azure OpenAI.

```powershell
cd agent-framework
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# .env (one-time)
@"
AZURE_OPENAI_ENDPOINT=https://<your-aoai>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21
"@ | Set-Content .env -Encoding ASCII

# one-shot
.\.venv\Scripts\python run_once.py "Customer wants a Foundry POC milestone next week"

# REPL
.\.venv\Scripts\python chat.py

# evals
.\.venv\Scripts\python eval_runner.py
```

**Auth**: `DefaultAzureCredential` → uses your `az login`. Needs `Cognitive Services OpenAI User` on the AOAI account.

---

## Option 2 — `foundry/` (Azure AI Foundry connected agents)

Registers each agent in `agents/` as a Foundry agent and wires them as **connected agents** under the orchestrator.

```powershell
cd foundry
pip install -r requirements.txt

$env:PROJECT_ENDPOINT  = "https://<your-foundry>.services.ai.azure.com/api/projects/<project>"
$env:MODEL_DEPLOYMENT  = "gpt-4o"

python register_agents.py            # one-time: creates 10 agents in Foundry
python invoke.py "Customer wants a Foundry POC milestone next week"
python eval_runner.py                # optional
python cleanup.py                    # tear down agents
```

**Auth**: `DefaultAzureCredential` → needs `Azure AI User` on the Foundry project.

---

## Option 3 — `copilot-studio/` (paste-ready instructions)

Generates the per-agent "Instructions" text you paste into Copilot Studio agents.

```powershell
cd copilot-studio
python build_assets.py
# Output: build/orchestrator.md + build/agents/*.md
```

Then in [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com): create one orchestrator agent + 10 specialist agents (or use the simpler single-agent pattern), paste each `build/*.md` into the agent's **Instructions**, and wire specialists as **Connected Agents** with the descriptions from [`copilot-studio/agent-descriptions.yaml`](copilot-studio/agent-descriptions.yaml).

See [`copilot-studio/README.md`](copilot-studio/README.md) for both single-agent and multi-agent patterns.

---

## Hosting `agent-framework/` on Azure

Use [Azure Architecture Factory (AAF)](https://github.com/fbabaei_microsoft/azure-architecture-factory) to wrap this runtime as a Container App with Key Vault + Managed Identity + App Insights — no agent code changes. See `azure-architecture-factory/projects/csa-helper-runtime/` for a reference deployment.

---

## Verifying success

A working call returns a non-empty `trace` containing `security_sentinel` first, then a relevant specialist (e.g. `milestone_coach`, `vbd_planner`, `ai_apps_architecture`):

```json
{
  "answer": "...",
  "trace": [
    {"agent": "security_sentinel", "request": "..."},
    {"agent": "milestone_coach",   "request": "..."}
  ]
}
```
