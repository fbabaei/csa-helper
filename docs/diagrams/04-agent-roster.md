# CSA Helper — Agent Roster

```mermaid
flowchart TB
    subgraph Core
      O[01 CSA Orchestrator]
      S[00 Security Sentinel]
    end

    subgraph Discovery
      I[02 Engagement Intake & Outcomes]
      M[03 Milestone Coach]
    end

    subgraph Planning
      V[04 VBD Planner]
      D[05 Delivery Request Navigator]
    end

    subgraph Architecture
      AA[06 AI Apps Architecture]
      SA[07 Security Architecture & Readiness]
    end

    subgraph Execution
      EH[08 Execution Hygiene]
      PE[09 Post-Delivery Expansion]
      IR[10 Impact Reporting]
    end

    O --- S
    O --> I
    O --> M
    O --> V
    O --> D
    O --> AA
    O --> SA
    O --> EH
    O --> PE
    O --> IR
```
