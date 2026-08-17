# Interview Pitch: Governed Payer Clinical Intelligence Fleet

**Project Title:** Governed Payer Clinical Intelligence Fleet (`payer-clinical-intelligence`)  
**Tech Stack:** Google GenAI SDK (Gemini 3.5 Flash / Vertex AI), Google ADK Framework, FastAPI, PostgreSQL (Cloud SQL), Terraform, OpenTelemetry, Streamlit  
**Live Demo:** [https://payer-clinical-intelligence.streamlit.app/](https://payer-clinical-intelligence.streamlit.app/)  
**GitHub:** [https://github.com/sechan9999/payer-clinical-intelligence](https://github.com/sechan9999/payer-clinical-intelligence)

---

## ⚡ 1. 30-Second Elevator Pitch

> "I built the **Governed Payer Clinical Intelligence Fleet** — a multi-agent AI system designed for healthcare payers and providers to automate prior authorizations, claim denial appeals, and clinical care gap analysis. 
> 
> Most enterprise AI projects fail because of security concerns: prompt injection, PHI leaks, or LLMs taking unauthorized actions. I inverted the design philosophy: **instead of asking 'how autonomous can the agent be?', I asked 'what is the agent structurally unable to do?'** 
> 
> By enforcing security at the Python function signature, SQL database pre-filtering, and HTTP approval gate layers rather than relying on prompt instructions, I built a zero-trust multi-agent fleet on Gemini 3.5 Flash and Google ADK that achieves 100% security denial accuracy and 0% unauthorized dispatch rate."

---

## 🔬 2. 2-Minute Technical Deep Dive (For Tech Leads & AI Architects)

> "In healthcare administrative workflows, Prior Authorization and Denial Appeals cost over $30B annually in manual friction. However, standard RAG or autonomous agents can't be deployed because of strict HIPAA/PHI rules and financial contract confidentiality.
> 
> To solve this, I designed a multi-agent system on **Gemini 3.5 Flash and Google Agent Development Kit (ADK)** with **3 immutable code-enforced guarantees**:
> 
> 1. **Server-Derived Role Immutability**: No tool in the codebase accepts a `role`, `identity`, or `employee_id` parameter. User roles are derived server-side from `X-Fleet-Token` headers. The LLM literally lacks the vocabulary to claim or escalate permissions. A unit test asserts this across every tool signature using Python reflection.
> 2. **SQL Pre-Filtering Before Ranking**: Document authorization isn't requested in a prompt or filtered after retrieval. A SQL `WHERE` clause filters out unauthorized rows *first*. Restricted documents (like confidential fee schedules) never enter the application context, preventing prompt leakage or accidental LLM hallucination.
> 3. **Isolated Human Approval Gate & Autonomy Grades**: Agents handling sensitive actions (prior auth submissions or patient outreach) are assigned an autonomy grade of `drafts_only`. Sending and dispatching tools do not exist in the agent's tool catalog — they are HTTP-only endpoints that refuse with an **HTTP 409 Conflict** if no human supervisor has signed off.
> 
> The system runs on Google Cloud Platform with **Cloud Run (scale-to-zero)**, **Cloud SQL (PostgreSQL 15)** with dual sync (`pg8000`) and async (`asyncpg`) drivers, **Pub/Sub** event streams, and **Secret Manager**, backed by an interactive 5-tab Streamlit dashboard and OpenTelemetry tracing."

---

## 🎯 3. The STAR Method Story (Behavioral Interview Framing)

### **Situation**
Healthcare enterprise clients want to modernize prior authorization and claims adjudication using multi-agent AI. However, existing LLM solutions fail security audits due to vulnerability to prompt injection, privilege escalation, and unapproved external actions.

### **Task**
Design and build a production-shaped, production-ready multi-agent fleet over a dual Payer and Clinical RAG layer on Gemini 3.5 Flash and Google Cloud, proving zero unauthorized data access or action execution.

### **Action**
- Architected 2 domain agents (`payer_intelligence`, `clinical_growth`) under a central `FleetCoordinator` using Google ADK and `google-genai` SDK.
- Implemented **SQL-level security pre-filtering** (`permitted_documents()`) to isolate confidential Payer fee schedules from Clinicians prior to semantic ranking.
- Built an **Isolated Human Approval Gate** where sensitive actions are queued in a `PENDING` state and require HTTP sign-off from a Medical Director, returning **HTTP 409 Conflict** on premature attempts.
- Wrote full **Terraform IaC** for GCP (Cloud Run, Cloud SQL, Pub/Sub OIDC push, Secret Manager, IAM `serviceAccountTokenCreator`).
- Created a 15-test quantitative benchmark suite testing Citation Precision, Security Isolation, Guardrail Interception, and Gate Determinism.

### **Result**
- **100% Citation Precision** on policy and clinical guidance queries.
- **100% Security Denial Accuracy** (zero unauthorized document leaks across roles).
- **100% Prompt Injection Interception** prior to model/database execution.
- Deployed a live interactive Streamlit dashboard at [`payer-clinical-intelligence.streamlit.app`](https://payer-clinical-intelligence.streamlit.app/) and published open-source code on GitHub.

---

## ❓ 4. Anticipated Interview Questions & Bulletproof Answers

### Q1: "Why not just tell the model in its system prompt to obey role permissions?"
> **Answer:** "System prompt instructions are a courtesy to the model, not a security boundary. The moment a user submits a prompt injection attack like 'ignore all previous instructions', prompt-level constraints break down. By enforcing security in Python function signatures, SQL predicates, and HTTP gate endpoints, the security contract remains 100% intact even if the LLM is completely compromised."

### Q2: "How did you handle the dual database driver requirement for Cloud SQL?"
> **Answer:** "Google ADK's `DatabaseSessionService` runs on SQLAlchemy's `asyncio` extension and requires an async driver (`postgresql+asyncpg`), whereas synchronous application code uses `postgresql+pg8000`. `asyncpg` expects the Cloud SQL socket *directory* path (`/cloudsql/INSTANCE`), while `pg8000` expects the socket *file* path (`/cloudsql/INSTANCE/.s.PGSQL.5432`). I built a centralized connection manager in `app/config.py` that handles dual driver resolution and includes password redaction for Cloud Logging."

### Q3: "How do you ensure zero LLM hallucinations in medical policy answers?"
> **Answer:** "We enforce Extractive Citation Guardrails (`app/guardrails.py`). Every answer generated by Gemini 3.5 Flash must explicitly tag the exact Document ID (e.g. `[PAY-POL-101]`) retrieved from the permitted context set. If no permitted document contains the answer, the agent is programmed to state 'No authorized reference document found' rather than synthesizing ungrounded claims."

---

## 🛠️ 5. Key Architecture Resume Bullets

- **Architected a Governed Multi-Agent AI System** on **Gemini 3.5 Flash** and **Google ADK**, enforcing zero-trust role-based access control (RBAC) across Payer policy and Clinical guideline RAG databases.
- **Engineered Code-Level Security Guardrails** featuring server-derived identity tokens (`X-Fleet-Token`), SQL-level pre-retrieval filtering, prompt injection interception, and HTTP 409 Conflict approval gates.
- **Deployed Enterprise GCP Infrastructure** via **Terraform** including Cloud Run (scale-to-zero), Cloud SQL PostgreSQL 15 (dual `asyncpg`/`pg8000` drivers), Secret Manager, and OIDC-authenticated Pub/Sub event streams.
- **Built & Deployed Real-Time Monitoring Dashboard** on Streamlit Community Cloud featuring 5 interactive tabs for fleet queries, SQL RBAC visualizer, human approval queue, and OpenTelemetry audit trail.
