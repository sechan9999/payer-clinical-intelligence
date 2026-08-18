# 🎙️ 4-Minute English Demo Video Narration Script

**Project Title:** Governed Payer Clinical Intelligence Fleet (`payer-clinical-intelligence`)  
**Target Duration:** 04:00 (240 Seconds)  
**Tone:** Authoritative, Professional, Engineering-Focused, Executive-Ready  
**Live Demo App:** [https://payer-clinical-intelligence.streamlit.app/](https://payer-clinical-intelligence.streamlit.app/)

---

## 🎬 SCENE 1: Introduction & The Inverted Design Philosophy (00:00 - 00:30)

**[Visual Cue]**  
*Screen opens on the Streamlit Dashboard (`http://localhost:8501`). Camera pans across the top metric cards showing "Server Status: ONLINE", "Active Fleet Agents: 3", and "Compliance Rate: 100%".*

**[Voiceover Narration]**  
> "Welcome. Every enterprise AI demo asks the same question: *'How much can the agent do on its own?'* 
> 
> But in healthcare administration — where prior authorization backlogs and claim denial appeals cost over thirty billion dollars annually — that is the wrong question. A health plan or hospital network cannot survive an AI agent leaking PHI across roles, or emailing a patient an unapproved care plan.
> 
> So we inverted the design: **This project is not interesting because the agents are autonomous. It is interesting because of what they are structurally unable to do — and because those limits are enforced in code rather than requested in a prompt.**"

---

## 🎬 SCENE 2: Clinical Command Ledger & Agent Registry (00:30 - 01:15)

**[Visual Cue]**  
*Camera focuses on the Sidebar Persona Switcher (`tok-payer-admin`, `tok-clinician`, `tok-medical-director`) and expands the '🏷️ Agent Autonomy Grades' panel showing `Payer Intelligence` (`drafts_only`), `Clinical & Growth` (`drafts_only`), and `Coordinator` (`read_only`).*

**[Voiceover Narration]**  
> "Here in our **Clinical Command Ledger**, we inspect our Fleet Agent Registry. Every agent advertises its scope and explicit autonomy grade. 
> 
> Notice that both the Payer Intelligence Agent and Clinical Growth Agent are registered strictly as **'drafts_only'**. Zero tools in their catalog contain 'send' or 'dispatch' in their names. 
> 
> Crucially, **roles are server-derived**. Authentication tokens are passed via the `X-Fleet-Token` header. No tool function accepts a `role` or `employee_id` parameter. The Gemini model literally lacks the vocabulary to claim or escalate permissions, guaranteed by automated reflection tests across every Python function signature."

---

## 🎬 SCENE 3: Event Stream Routing, SQL Pre-Filtering & Gemini 3.5 Grounding (01:15 - 02:00)

**[Visual Cue]**  
*Clicks on '💬 Fleet Chat & Execution' tab. Selects preset query: "Prior Authorization rules for Cardiac MRI CPT 75561". Hits 'Execute Fleet Query'. Shows output response with explicit citation tags `[PAY-POL-101]` and expands raw execution telemetry.*

**[Voiceover Narration]**  
> "Now let's trace a query through our asynchronous event stream. When a claim event or policy query arrives, the Fleet Coordinator routes it through a strict **Two-Stage Retrieval Pipeline**. 
> 
> **Stage 1 is security**: A SQL `WHERE` predicate executes first, filtering out unauthorized documents before rows enter memory. If a Clinician requests confidential Payer fee schedules, they receive an empty set — not a model-composed refusal. 
> 
> **Stage 2 is quality**: Vector cosine similarity ranks the permitted candidates, and **Gemini 3.5 Flash through Vertex AI** synthesizes a grounded answer. Every response MUST cite its source document ID, such as `[PAY-POL-101]`, enforcing 100% grounded precision."

---

## 🎬 SCENE 4: Human Approval Gate & HTTP 409 Conflict Interception (02:00 - 02:45)

**[Visual Cue]**  
*Navigates to '🚦 Human Approval Queue' tab. Queues a new Prior Authorization draft for CPT 75561. Clicks 'Attempt Dispatch Prematurely' button. Red banner pops up showing `🚫 HTTP 409: Conflict: Approval ID 'appr-xxx' is in 'pending' state. Human sign-off required prior to dispatch.`*

**[Voiceover Narration]**  
> "Next, let's look at how we protect external communications using our **Isolated Human Approval Gate**. 
> 
> The Payer Agent drafts a Prior Authorization packet complete with an HL7 FHIR v4 Claim Bundle. But drafting is the end of its reach. Sending and dispatching are HTTP-only endpoints completely absent from the agent's tool set. 
> 
> Watch what happens when an unapproved premature dispatch is attempted: **The system refuses with an HTTP 409 Conflict error.** No unapproved draft can ever reach a patient or payer."

---

## 🎬 SCENE 5: Medical Director Approval, Audit Trail & Bulk Dry-Run Engine (02:45 - 03:30)

**[Visual Cue]**  
*Switches persona to `tok-medical-director` (Dr. Arthur Pendelton). Clicks 'Approve Item' then 'Dispatch Item'. Shows green success banner. Switches to '🖥️ Real-Time Server Monitor' tab and clicks 'Execute Bulk Simulation (3 Claims)'.*

**[Voiceover Narration]**  
> "Now, our Chief Medical Officer logs in via server identity. As a human supervisor, Dr. Pendelton inspects the HL7 FHIR bundle and clicks **'Approve'** followed by **'Dispatch'**. The action executes via HTTP status 200. 
> 
> In addition, our **Bulk Dry-Run Simulation Engine** allows medical operations teams to stress-test batch claim denial events prior to production, verifying zero unapproved dispatches across thousands of records. 
> 
> 100% of these interactions — including security refusals and role blocks — are written to an append-only Audit Log."

---

## 🎬 SCENE 6: Prometheus Stream Health & Conclusion (03:30 - 04:00)

**[Visual Cue]**  
*Highlights the Prometheus Stream Metrics block (`/metrics`), showing `fleet_stream_health_ratio 1.0`, `fleet_security_denials_total`, and SSE Inbox Sync status. Concludes on the GitHub repository page.*

**[Voiceover Narration]**  
> "Finally, our `/metrics` endpoint exposes real-time **Prometheus Stream Health and Threshold Monitoring**, tracking stream compliance ratios and active agent counts for OpenTelemetry dashboarding. 
> 
> By combining Gemini 3.5 Flash, Google ADK, server-derived RBAC, SQL pre-filtering, and HTTP 409 approval gates, we built a zero-trust multi-agent system that proves security in code. 
> 
> Try the live app at `payer-clinical-intelligence.streamlit.app`. Thank you!"
