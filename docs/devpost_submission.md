# Governed Payer Clinical Intelligence Fleet

## Inspiration

Healthcare payers (insurers) and clinical provider networks lose over $30B annually to manual administrative friction — from prior authorization backlog and claim denial appeal processing to missed quality care gaps. Nurses, claims specialists, medical directors, and growth managers spend hours digging through disparate CPT/ICD-10 coding guidelines, clinical practice manuals, and confidential fee schedules.

They are exactly the kind of organization multi-agent AI should help.

They are also the kind of organization that cannot survive an agent accidentally leaking PHI across roles, emailing a patient an unapproved care plan, or handing a clinician a Payer's confidential contracted rate sheet. Every agent demo we looked at answered "how much can it do on its own?" Nobody was answering "what is it structurally unable to do?" — which is the only question a healthcare organization with strict HIPAA and compliance mandates can actually act on.

So we inverted the pitch. This project is not interesting because the agents are autonomous. It is interesting because of what they are prevented from reaching, and because those limits are enforced in code rather than requested in a prompt.

## What it does

Payer Clinical Intelligence Fleet is a governed multi-agent intelligence system running off a shared event stream, Clinical Command Ledger, and auditable RAG layer over Payer policies and Clinical guidelines.

- **Payer Intelligence Agent** analyzes coverage rules, CPT 75561 criteria, fee schedules, denial appeal strategies, HL7 FHIR v4 bundles, and queues prior auth drafts (`drafts_only`).
- **Clinical & Growth Agent** analyzes ACC/AHA guidelines, HEDIS care gaps, care pathways, FHIR observations, and queues outreach initiatives (`drafts_only`).
- **Fleet Coordinator Agent** routes cross-domain queries while passing down server-derived user identity (`read_only`).

A business event — such as an incoming claim denial (`CLAIM_DENIED`) — writes its record and an `Activity` event in the same transaction. That event goes to Pub/Sub, gets pushed to the service, and the agent that owns that event type picks it up. Nobody is waiting at a prompt.

**The Compelling Vertical Healthcare Workflow:**
1. **Asynchronous Event Routing**: A claim denial event (`CO-50`, Claim `CLM-9921`) arrives on the event stream.
2. **Two-Stage SQL Pre-Filtering**: The **Payer Intelligence Agent** receives the event and queries permitted policy documents via SQL pre-filtering (`PAY-POL-101`), isolating confidential contract rates.
3. **Gemini Grounded Summarization**: Gemini 3.5 Flash synthesizes a grounded appeal package with explicit document citations (`[PAY-POL-101]`).
4. **HL7 FHIR v4 Bundle Draft (`drafts_only`)**: The agent generates a compliant HL7 FHIR v4 Claim Bundle (`Bundle`, `CoverageEligibilityRequest`, `Claim`, `Patient`).
5. **Human Approval Gate & HTTP 409 Refusal**: The package is queued in the isolated Human Approval Gate (`PENDING`). An attempted premature send by an unapproved caller returns **HTTP 409 Conflict**.
6. **Medical Director Sign-Off**: The Medical Director inspects the HL7 FHIR bundle in the Streamlit dashboard and authorizes dispatch via HTTP (Status 200).
7. **Bulk Dry-Run Simulation Engine**: Operations teams execute batch dry-runs over hundreds of claims to verify zero unapproved dispatches.
8. **SSE Live Inbox Stream**: Real-time Server-Sent Events push pending approval counts and notifications to connected clinical dashboards.
9. **Prometheus Stream Health & Threshold Monitoring**: Exposes `/metrics` tracking stream health ratios (`fleet_stream_health_ratio`) and security denial counts for OpenTelemetry dashboarding.

Three guarantees hold regardless of what anyone types:

**Roles are server-derived (`X-Fleet-Token`).** No tool accepts a role, identity, or employee id argument, so the model has no vocabulary for claiming one. A test asserts this across every tool signature, which means the guarantee survives future changes rather than resting on discipline.

**Retrieval is filtered in SQL.** A clinician asking for confidential Payer rate sheets gets nothing — not a refusal message the model composed, but an empty result, because the document was excluded by a `WHERE` clause before any row existed. Filtering is security and runs first; vector cosine similarity ranking is quality and runs afterwards on the permitted set only.

**Nothing reaches a patient or payer unapproved.** The payer and clinical agents can queue a draft and that is the end of their reach. Approving and sending are HTTP endpoints, absent from every agent's tool set, and `send()` refuses with an **HTTP 409 Conflict** if no human signed off.

Around that sit an Agent Registry that publishes each agent's version, scope, and *autonomy grade*; an inline guardrail plugin that blocks prompt injection before the model is called; and an append-only audit trail plus OpenTelemetry spans that record refusals with the same weight as successes.

## How we built it

**Gemini 3.5 Flash through Vertex AI**, pinned rather than aliased — using the official `google-genai` SDK (`from google import genai`) with grounded synthesis over permitted context documents.

**Google ADK** with the A2A template. The agents are ADK agents under a coordinator; the deployed service publishes an A2A agent card (`/.well-known/agent.json`) advertising every agent, skill, and dynamic runtime status. A `BasePlugin` carries the guardrail, registered on the `App` so it covers every agent at once.

**Google Cloud**: Cloud Run with scale-to-zero (`min_instances = 0`), Cloud SQL Postgres for state with `pg8000` sync and `asyncpg` async dual drivers and `pg8000.enable_pgvector` support, Pub/Sub with an OIDC-authenticated push subscription, Secret Manager for database credentials, Model Armor for guardrails with a heuristic fallback, Cloud Trace for spans, HL7 FHIR v4 Bundle builder (`app/fhir.py`), Prometheus Metrics exporter (`/metrics`), SSE Live Inbox Stream (`/fleet/inbox/sse`), and a 5-tab Streamlit Web Dashboard ([https://payer-clinical-intelligence.streamlit.app/](https://payer-clinical-intelligence.streamlit.app/)).

We kept one rule throughout: **the whole system runs offline with no credentials.** SQLite stands in for Cloud SQL and a heuristic screen stands in for Model Armor, so all 13 unit tests and 15 evaluation benchmark tests — including every access-control, FHIR bundle, and human-gate assertion — run on a laptop with no cloud project. A reviewer can verify the claims before deciding whether to trust the demo.

## Challenges we ran into

**We leaked a database password into Cloud Logging.** A failed connection raises with the full URL in the exception message, and our handler logged the exception with a traceback. We caught it while reading startup logs, rotated the password, and added `redact_url()` that every log site touching a URL now passes through. The handler logs the exception *type* now, never the exception. It was the most useful bug of the project: we were writing an access-control system and had a credential in plain text three layers down.

**ADK's session store and our repository code cannot share a driver.** The session service runs on SQLAlchemy's asyncio extension and rejects a synchronous driver outright; our own code is synchronous. The fix is two URLs against the same database — `asyncpg` for sessions, `pg8000` for everything else — and they differ in a way that is easy to miss: asyncpg wants the socket *directory*, pg8000 wants the socket *file*.

**Cloud Run's IAM layer eats the `Authorization` header.** We were passing employee tokens there, and behind an authenticated ingress every governance endpoint returned 401 while working perfectly in tests. Identity moved to `X-Fleet-Token`.

**Pub/Sub push subscription failed delivery with 401.** Creating a push subscription to a private Cloud Run service succeeded, but every delivery failed with 401. Pub/Sub's own service agent required `roles/iam.serviceAccountTokenCreator` on the push service account identity in Terraform (`iam.tf`).

## Accomplishments that we're proud of

**100% Score on Quantitative Evaluation Benchmark.** We built a 15-test quantitative benchmark suite (`tests/eval/eval_benchmark.py`) testing Citation Precision (100%), Security Denial Accuracy (100%), Prompt Injection Interception (100%), and Human Gate Determinism (100%).

**The demo shows refusals and HTTP 409 Conflicts.** Our proof script (`demo.py`) and video demonstrate intentional failures: a guardrail blocking before the model, a tool refusing a department, an HTTP 409 Conflict on an unapproved send, and a denial in the audit log. Anyone can film an agent succeeding.

**The registry publishes what each agent may not do.** Version, domain, capabilities, and restrictions — plus an autonomy grade of `autonomous`, `drafts_only`, or `read_only`. A test asserts the `payer_intelligence` and `clinical_growth` agents are registered as `drafts_only` and that no tool with "send" in its name is listed, so the catalogue cannot advertise a capability the code does not permit.

**Denials are first-class in telemetry.** A refused call sets `fleet.access_denied = True` on its OpenTelemetry span, so refusals are findable in Cloud Trace without constructing a filter.

## What we learned

**Filtering and ranking must be separate things.** Once we split them, the security property stopped depending on retrieval quality. We can swap keyword matching for pgvector embeddings tomorrow without touching the boundary, because the boundary is a SQL predicate that runs first.

**A guarantee the model is asked for is not a guarantee.** We wrote the restrictions into every agent's instruction *and* enforced them in Python. When we tested the injection attempt, the instruction was irrelevant — the guardrail stopped it before the model was called, and the tool ACL would have stopped it after. The instruction is a courtesy; the code is the contract.

**Silent fallbacks are worse than failures.** We built dynamic runtime environment reporting (`check_runtime_environment()`) so the system transparently reports whether it is running on Vertex AI with Cloud SQL or offline Extractive RAG with SQLite, avoiding fake `True` booleans.

**Write the offline path first.** Making the entire system runnable without credentials was not a testing convenience — it forced every cloud dependency behind a port, which is why swapping the LLM provider, database engine, and guardrail backend each turned out to be a one-file change.

## What's next for Payer Clinical Intelligence Fleet

**Native Cloud SQL pgvector Scaling.** Migrate in-memory vector similarity ranking directly into Cloud SQL PostgreSQL `pgvector` distance queries (`<=>`).

**Live Epic & Cerner EHR Webhooks.** Expand the SSE Live Inbox into native EHR InBasket approval webhooks for Medical Directors.

**Split an agent across a process boundary.** Currently, agents run as sub-agents in one service. Deploying `payer_intelligence` as its own standalone A2A microservice will let Payer IT own its deployment independently from Clinical networks.
