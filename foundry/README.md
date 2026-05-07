# CSA Helper on Microsoft Foundry — Example

This folder shows how to run the CSA Helper agent set on **Microsoft Foundry**
(Azure AI Foundry / azure-ai-projects SDK) using the **Connected Agents**
pattern: the **CSA Orchestrator** is the user-facing agent, and every other
agent in `../agents/` is registered as a connected sub-agent it can call as a
tool.

```
                 +------------------------+
   user ----->   |  CSA Orchestrator (01) |  <-- entry point
                 +-----------+------------+
                             |
        +--------+-----------+-----------+--------+
        v        v           v           v        v
   sentinel   intake     vbd_planner   ...     impact_reporting
     (00)      (02)         (04)                   (10)
```

The Security Sentinel (`00`) is wired as a connected agent the orchestrator
**must** call before any specialist when the request looks security-sensitive
(see the orchestrator's system prompt).

---

## Prerequisites

1. An **Azure AI Foundry project** with a chat model deployment (e.g. `gpt-4o`,
   `gpt-4o-mini`, `gpt-4.1`).
2. Your account assigned **Azure AI User** (or higher) on the project.
3. Python 3.10+.
4. Logged in: `az login`.

Install deps:

```powershell
pip install -r requirements.txt
```

Set environment variables (PowerShell):

```powershell
$env:PROJECT_ENDPOINT = "https://<your-foundry-account>.services.ai.azure.com/api/projects/<your-project>"
$env:MODEL_DEPLOYMENT_NAME = "gpt-4o-mini"
```

> Find `PROJECT_ENDPOINT` in the Foundry portal → your project → **Overview** →
> *Project endpoint*.

---

## Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python deps (`azure-ai-projects`, `azure-identity`) |
| `register_agents.py` | Reads `../agents/*.md` + `../manifests/csa-helper-manifest.yaml`, creates one Foundry agent per file, then creates the **CSA Orchestrator** with all the others wired as connected-agent tools. Writes the orchestrator id to `.agent_ids.json`. |
| `invoke.py` | Loads `.agent_ids.json`, opens a thread, sends a user prompt to the orchestrator, prints the assistant reply. |
| `cleanup.py` | Deletes every agent recorded in `.agent_ids.json` from the Foundry project. |
| `eval_runner.py` | Runs every scenario in `../eval/*.md` against the orchestrator, scores each with an LLM judge (Azure OpenAI), writes `eval_results.json`. |

---

## Run

```powershell
# 1. Create the agents in Foundry (one-time)
python register_agents.py

# 2. Ask the orchestrator something
python invoke.py "Customer wants to pilot an AI agent in 6 weeks. Help me scope outcomes."

# 3. Try a security-sensitive prompt — sentinel should engage
python invoke.py "I want to share a customer's prod log file with my teammate, can you help?"

# 4. Run the eval pack
$env:JUDGE_OPENAI_ENDPOINT          = "https://<your-aoai>.openai.azure.com/"
$env:JUDGE_MODEL_DEPLOYMENT_NAME   = "gpt-4o"
python eval_runner.py

# 5. Tear it down
python cleanup.py
```

---

## What `register_agents.py` does

1. Loads `../manifests/csa-helper-manifest.yaml`.
2. For each entry:
   - Reads the prompt body from the linked `../agents/*.md` file.
   - Calls `agents.create_agent(...)` with that body as `instructions`.
3. Builds a `ConnectedAgentTool` for every non-orchestrator agent.
4. Re-creates the orchestrator with all those connected-agent tools attached
   so it can dispatch via tool calls.
5. Persists `{ "orchestrator_id": "...", "all_ids": [...] }` to
   `.agent_ids.json` for `invoke.py` and `cleanup.py`.

---

## Notes

- This is the **hosted-agent** path; nothing runs locally except the SDK
  client. Conversations and runs are managed by Foundry.
- `eval_runner.py` is a lightweight LLM-as-judge harness for the cases in
  `../eval/`. For larger eval suites you can also use Foundry's hosted batch
  evaluation against the same orchestrator id.
- To upgrade prompts, edit the markdown under `../agents/`, then re-run
  `cleanup.py` followed by `register_agents.py`. (A future enhancement could
  patch in place via `agents.update_agent`.)
