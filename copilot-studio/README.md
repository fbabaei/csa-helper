# CSA Helper on Microsoft Copilot Studio

Bring the same orchestrator + 10 specialist agents from `agents/` into
[Microsoft Copilot Studio](https://copilotstudio.microsoft.com) as a multi-agent
solution.

Copilot Studio supports two patterns. Pick the one that matches your tenant:

| Pattern | When to use | What you build |
|---|---|---|
| **A. Single agent (inlined)** | Fastest. One agent that contains the orchestrator prompt and routes by describing the specialists in its instructions. | 1 custom agent. |
| **B. Multi-agent (connected agents)** | Production. Each specialist is its own agent and the orchestrator delegates via Copilot Studio's *Connected agents* feature (GA 2025+). | 1 orchestrator + 10 specialists, wired together. |

---

## Files

| File | Purpose |
|---|---|
| `build_assets.py` | Reads `manifests/csa-helper-manifest.yaml` and `agents/*.md`, emits per-agent paste-ready instructions under `copilot-studio/build/`. |
| `agent-descriptions.yaml` | One-line descriptions used as the *handoff description* on each connected agent (what triggers routing). |
| `topics/escalate-to-security.yaml` | Sample Copilot Studio topic that triggers a hand-off to **Security Sentinel** when the user mentions data, secrets, or customer info. Import-ready. |

> `build/` is generated and gitignored.

---

## Build the paste-ready assets

```powershell
cd C:\Users\fbabaei\workspace\csa-helper\copilot-studio
python build_assets.py
```

This produces:

```
build/
  orchestrator.md          # paste into the orchestrator agent's "Instructions"
  agents/
    00-security-sentinel.md
    02-engagement-intake-outcomes.md
    ...
    10-impact-reporting.md
  combined-single-agent.md # Pattern A: everything inlined into one agent
```

---

## Pattern A — Single agent (5 minutes)

1. Copilot Studio → **Create** → **New agent** → skip the wizard (*Configure manually*).
2. Name: `CSA Helper`. Description: *Routes Cloud Solution Architect requests to the right specialist playbook.*
3. **Instructions**: paste the contents of `build/combined-single-agent.md`.
4. **Knowledge**: (optional) upload the `docs/` folder so the agent can ground answers in CSA templates.
5. **Test** in the right-hand pane:
   > *"Customer wants to commit a Foundry POC milestone next week — what's the plan?"*

That's it. No connected agents required.

---

## Pattern B — Multi-agent with Connected Agents

### 1. Create the 10 specialist agents

For each file in `build/agents/*.md`:

1. Copilot Studio → **Create** → **New agent** → *Configure manually*.
2. Name = the H1 from the file (e.g. `Security Sentinel`).
3. **Description** = the matching value from `agent-descriptions.yaml` (this is what the orchestrator uses to decide when to hand off — keep it crisp).
4. **Instructions** = full file contents.
5. (Optional) **Knowledge** = upload `docs/` and `eval/`.
6. **Publish**.

### 2. Create the orchestrator

1. New agent named `CSA Orchestrator`.
2. **Instructions** = `build/orchestrator.md`.
3. Open **Agents** (left nav inside the orchestrator) → **Add a connected agent** → pick each of the 10 specialists.
4. For each connected agent confirm the description matches `agent-descriptions.yaml` — that's what the LLM sees when routing.

### 3. (Optional) Add the security guard topic

Settings → **Topics** → **Add** → **From file** → select
`topics/escalate-to-security.yaml`. This forces a hand-off to `Security Sentinel`
whenever the user mentions secrets/PII/customer data, even if the model would
have skipped it.

### 4. Publish

**Publish** → choose channels (Teams, M365 Copilot, custom website, etc.).

---

## Tips

- Copilot Studio's connected-agents router is generative; the **description**
  on each connected agent is the most important field. `agent-descriptions.yaml`
  is the single source of truth — re-run `build_assets.py` after editing it.
- Keep instructions under ~8k chars per agent. The originals in `agents/*.md`
  are already well within that.
- For evaluation in Copilot Studio, use the built-in **Test** pane plus the
  *Generative answers* analytics, or run the standalone harness in
  [`../foundry/eval_runner.py`](../foundry/eval_runner.py) against an exported
  endpoint.
