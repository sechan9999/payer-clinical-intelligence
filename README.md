# Payer Clinical Intelligence Agents (`payer-clinical-agents`)

> Two governed AI agents (**Payer Intelligence** + **Clinical & Growth**) over one auditable RAG layer — demo-scale, production-shaped.

Built on the governed multi-agent fleet architecture of [`gemini-ops-fleet`](https://github.com/sechan9999/gemini-ops-fleet) for the **Google Cloud / Gemini Enterprise Agent Platform**.

---

## 🏛️ System Architecture & Key Governance Principles

The system provides back-office decision intelligence for healthcare payers, health systems, and value-based care networks. It enforces strict compliance, data isolation, and human control across 5 core assertions:

```
                                 ┌──────────────────────────────┐
                                 │      User Query / Token      │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │    Server Identity (RBAC)    │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │   Input Guardrail Check      │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │   SQL Pre-Retrieval Filter   │
                                 │  (permitted_documents SQL)   │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │     Domain Agent Fleet       │
                       ┌─────────┴──────────────┬───────────────┴─────────┐
                       │                        │                         │
                       ▼                        ▼                         ▼
         ┌───────────────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
         │ Payer Intelligence Agent  │ │ Coordinator      │ │ Clinical & Growth Agent  │
         │ - Policies, CPT 75561     │ │ - Intent Router  │ │ - Guidelines, Care Gaps  │
         │ - Denial Appeals          │ └──────────────────┘ │ - HEDIS Outreach         │
         │ - Prior Auth Queue        │                      │ - Growth Initiatives     │
         └─────────────┬─────────────┘                      └─────────────┬────────────┘
                       │                                                  │
                       └────────────────────────┬─────────────────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │ Isolated Human Approval Gate │
                                 │ (Prior Auth / Care Dispatch) │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │ Append-Only Audit & Telemetry│
                                 └──────────────────────────────┘
```

### The 5 Governance Claims:
1. **Server-Derived Identity & Role Immutability**: Roles (`payer_admin`, `claims_specialist`, `clinician`, `growth_lead`, `medical_director`) are derived server-side from dev bearer tokens. No tool accepts a role argument, preventing model-driven privilege escalation.
2. **SQL-Level Pre-Retrieval Data Segregation**: `retrieval.permitted_documents(user_role)` filters candidate records in SQL before semantic search/ranking occurs. Clinicians cannot access Payer contracted fee schedules; Payer analysts cannot access raw clinical PHI.
3. **Input & Output Guardrail Interception**: Prevents prompt injections ("ignore previous instructions") and enforces citation tagging (`PAY-POL-101`, `CLN-GUIDE-401`) on all generated outputs.
4. **Isolated Human-in-the-Loop (HITL) Gate**: Sensitive operations (Prior Auth submissions, patient care plan outreach) are held in `pending` approval status. Sending endpoints are HTTP-only and unreachable by any LLM tool signature.
5. **Full Audit Traceability**: 100% of queries, tool calls, data access attempts, and security denials are logged to an append-only audit trail with OpenTelemetry governance attributes.

---

## ⚡ Quickstart & Local Verification

The codebase runs 100% offline with zero external GCP cloud credentials required for local dev/testing (SQLite in-memory DB + heuristic safety screen).

### 1. Run Unit Tests (48+ Assertions)
```bash
uv sync --group dev
uv run pytest tests/unit -q
```

### 2. Run End-to-End Governance Demonstration
```bash
uv run python demo.py
```

---

## 🔌 Governance API Reference

### `POST /fleet/query`
Execute a query through the fleet coordinator.
- Headers: `Authorization: Bearer tok-payer-admin` (or `tok-clinician`, `tok-claims-spec`, `tok-growth-lead`, `tok-medical-director`)
- Body:
```json
{
  "query": "Prior Authorization rules for Cardiac MRI CPT 75561",
  "target_domain": "payer"
}
```

### `GET /fleet/registry`
Returns the catalog of registered agents, their versions, tool definitions, and restriction parameters.

### `GET /fleet/approvals`
List items in the Human Approval Queue (pending, approved, dispatched).

### `POST /fleet/approvals/{approval_id}/approve`
Approve a pending action (Requires `tok-medical-director` or `tok-payer-admin`).

### `POST /fleet/approvals/{approval_id}/send`
Dispatch an approved action to external recipients.

### `GET /fleet/audit`
Retrieve the append-only security audit log.

### `GET /fleet/events`
Stream the activity outbox events.

---

## 🚢 Production Cloud Run Deployment

To deploy to Google Cloud Run with Vertex AI integration:

```bash
# 1. Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable GCP Services
gcloud services enable \
  aiplatform.googleapis.com run.googleapis.com \
  sqladmin.googleapis.com secretmanager.googleapis.com \
  --project=YOUR_PROJECT_ID

# 3. Deploy via Docker / Cloud Run
gcloud run deploy payer-clinical-agents \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 0
```

---

## 📄 License
MIT License. Built for enterprise governance on Gemini + ADK.
