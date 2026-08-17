# Architecture Specification & System Diagrams

`payer-clinical-intelligence` is a governed multi-agent back-office intelligence system for healthcare payers and providers, built on **Gemini 3.5 Flash**, **Google Agent Development Kit (ADK)**, and **Google Cloud Platform (Cloud Run, Cloud SQL, Pub/Sub, Secret Manager)**.

---

## 🏗️ System Architecture & Data Flow

```mermaid
graph TD
    Client[Client / Web UI / A2A Inspector] -->|HTTP / X-Fleet-Token| Ingress[Cloud Run Ingress]
    
    subgraph Security & Governance Layer
        Ingress -->|1. Extract Identity| Identity[app/identity.py<br/>Server-Derived RBAC]
        Ingress -->|2. Validate Input| Guardrail[app/guardrails.py<br/>Model Armor / Injection Filter]
    end

    Guardrail -->|3. Route Query| Coordinator[app/fleet.py<br/>Fleet Coordinator Agent]

    subgraph Agent Fleet Layer
        Coordinator --> PayerAgent[Payer Intelligence Agent<br/>Autonomy Grade: drafts_only]
        Coordinator --> ClinicalAgent[Clinical & Growth Agent<br/>Autonomy Grade: drafts_only]
    end

    subgraph SQL Pre-Retrieval Isolation Boundary
        PayerAgent -->|4. Permitted Query| SQLFilter[app/retrieval.py<br/>permitted_documents SQL Filter]
        ClinicalAgent -->|4. Permitted Query| SQLFilter
        SQLFilter -->|SQL WHERE permitted_roles| CloudSQL[(Cloud SQL / SQLite<br/>Documents & Fee Schedules)]
    end

    subgraph Gemini 3.5 Model Inference Layer
        SQLFilter -->|5. Permitted Candidates Only| Gemini[Google GenAI SDK<br/>Gemini 3.5 Flash / Vertex AI]
    end

    subgraph Human Approval Gate & Audit Trail
        PayerAgent -->|Sensitive Action| ApprovalQueue[app/approvals.py<br/>Isolated Pending Queue]
        ClinicalAgent -->|Sensitive Action| ApprovalQueue
        ApprovalQueue -->|6. HTTP Only| HumanSupervisor[Medical Director / Human Supervisor]
        
        PayerAgent -->|7. Audit Log & Telemetry| AuditStore[(Audit Logs & Event Outbox)]
        ClinicalAgent -->|7. Audit Log & Telemetry| AuditStore
    end
```

---

## 🔒 3 Core Governance Patterns

### Pattern 1: Server-Derived Role Immutability
No tool accepts a `role`, `identity`, or `employee_id` parameter. The model has zero vocabulary for claiming or escalating access. Authentication tokens are derived server-side from `X-Fleet-Token` or `Authorization` headers.

```mermaid
sequenceDiagram
    participant User
    participant Route as FastAPI Route
    participant Identity as app/identity.py
    participant Tool as Agent Tool (tools.py)

    User->>Route: POST /fleet/query (Header: X-Fleet-Token)
    Route->>Identity: derive_identity(x_fleet_token)
    Identity-->>Route: UserIdentity (role=clinician)
    Route->>Tool: execute_tool(query, user_identity=derived_identity)
    Note over Tool: Tool inspects server-derived identity.<br/>No model argument can alter user_identity.
```

---

### Pattern 2: Separation of Security Filtering from Relevance Ranking

Security pre-filtering runs as a SQL `WHERE` clause BEFORE candidates enter semantic ranking. Restricted documents never enter memory, preventing prompt leakage or accidental citation.

```mermaid
graph LR
    Query[Incoming Search Query] --> SQL[SQL Pre-Filter<br/>WHERE permitted_roles LIKE %role%]
    SQL -->|Permitted Subset Only| Ranker[Semantic Keyword / Embedding Ranker]
    Ranker -->|Top-K Grounded Context| LLM[Gemini 3.5 Flash Inference]
```

---

### Pattern 3: Isolated Human Approval Gate (Pending $\rightarrow$ Approved $\rightarrow$ Dispatched)

Actions involving patient outreach or prior authorization filings are given an **Autonomy Grade of `drafts_only`**. Sending and dispatching paths are HTTP endpoints absent from all agent tool definitions. Premature dispatch attempts return **HTTP 409 Conflict**.

```mermaid
stateDiagram-v2
    [*] --> Pending: Agent calls queue_prior_auth_request()
    Pending --> Refused: Premature dispatch attempt (HTTP 409 Conflict)
    Pending --> Approved: Human supervisor calls POST /fleet/approvals/{id}/approve
    Approved --> Dispatched: Human supervisor calls POST /fleet/approvals/{id}/send
    Dispatched --> [*]
```

---

## ☁️ Google Cloud Infrastructure Layout

- **Cloud Run (v2)**: Stateless server container scaled to zero (`min_instances = 0`).
- **Cloud SQL (PostgreSQL 15)**: Dual database driver connection (`postgresql+pg8000` for sync repository, `postgresql+asyncpg` for async session store).
- **Pub/Sub**: Activity event outbox push subscription with OIDC authentication.
- **Secret Manager**: Secure storage for database passwords.
- **Vertex AI & Model Armor**: Pinned `gemini-3.5-flash` model inference and enterprise safety templates.
