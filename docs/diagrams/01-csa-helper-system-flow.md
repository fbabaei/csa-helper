# CSA Helper — System Flow

High-level routing across the CSA Helper agents. Every user request enters
through the **CSA Orchestrator**, which consults the **Security Sentinel**
before dispatching to a specialist agent.

```mermaid
flowchart TD
    User[CSA / Account Team] --> Orchestrator[CSA Orchestrator]

    Orchestrator -->|Security-sensitive?| Security[Security Sentinel]
    Security -->|Allowed| Orchestrator
    Security -->|Blocked| Stop[Stop / Redirect]

    Orchestrator --> Intake[Engagement Intake & Outcomes]
    Orchestrator --> Milestones[Milestone Coach]
    Orchestrator --> Delivery[VBD / Delivery Planner]
    Orchestrator --> Request[Delivery Request Navigator]
    Orchestrator --> Arch[AI Apps Architecture]
    Orchestrator --> SecArch[Security Architecture & Readiness]
    Orchestrator --> Closeout[Execution Hygiene]
    Orchestrator --> Expansion[Post-Delivery Expansion]
    Orchestrator --> Reporting[Impact Reporting]

    Stop --> User
```
