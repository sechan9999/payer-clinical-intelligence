# Payer Clinical Intelligence Agents (`payer-clinical-agents`)

> Two governed AI agents (**Payer Intelligence** + **Clinical & Growth**) over one auditable RAG layer — demo-scale, production-shaped.

Built on the governed multi-agent fleet architecture of [`gemini-ops-fleet`](https://github.com/sechan9999/gemini-ops-fleet) for the **Google Cloud / Gemini Enterprise Agent Platform** (The Fortified Enterprise Fleet Track).

---

## 💡 Inspiration & Core Philosophy

Most AI demos focus on "how much can the agent do on its own?" We inverted the question: **"What is the agent structurally unable to do?"** — which is the only question a healthcare organization with strict compliance mandates can actually act on.

This project is not interesting because the agents are autonomous. It is interesting because of what they are **prevented from reaching**, and because those limits are **enforced in code rather than requested in a prompt**.

---

## 🏛️ 3 Structural Guarantees

1. **Roles are Server-Derived (`X-Fleet-Token`)**: No tool accepts a role, identity, or employee ID argument. The model has zero vocabulary for claiming or escalating access. Authentication tokens are passed via `X-Fleet-Token` (or `Authorization`) headers.
2. **Retrieval is Filtered in SQL**: Filtering runs *first* as security (`retrieval.permitted_documents()`); semantic ranking runs afterwards on the permitted set only. Clinicians asking for Payer contract rates receive an empty set, not a model-composed refusal.
3. **Nothing Reaches External Recipients Unapproved**: Sensitive actions (Prior Auth submissions, patient care dispatches) are assigned an **Autonomy Grade of `drafts_only`**. Approving and sending are HTTP endpoints absent from every agent's tool set. A premature dispatch attempt returns **HTTP 409 Conflict**.

---

## 🏷️ Agent Autonomy Grades

Every agent advertises its autonomy level in the central registry ([`app/registry.py`](file:///C:/Users/secha/.gemini/antigravity-ide/scratch/payer-clinical-agents/app/registry.py)):

| Agent | Domain | Autonomy Grade | Key Capabilities & Restrictions |
| :--- | :--- | :--- | :--- |
| **Payer Intelligence** | `payer` | `drafts_only` | Policy RAG, CPT 75561 criteria, denial analysis, prior auth queueing. **Zero send/dispatch tools.** |
| **Clinical & Growth** | `clinical` | `drafts_only` | ACC/AHA guideline search, HEDIS care gaps, growth outreach queueing. **Zero send/dispatch tools.** |
| **Coordinator** | `cross_domain` | `read_only` | Cross-domain intent routing and server-derived identity propagation. |

---

## ⚡ Quickstart & Local Verification

The whole system runs 100% offline with zero cloud credentials required.

### 1. Run Unit Tests (11 Test Suites)
```bash
uv sync --group dev
uv run pytest tests/unit -v
```

### 2. Run End-to-End Governance Demonstration
```bash
uv run python demo.py
```

### 3. Run Interactive Streamlit Dashboard
```bash
uv run streamlit run app/dashboard.py
```

---

## 📜 Prior Art & Technical Disclosures

Per hackathon rules, all code in this repository was newly written during the Submission Period for the healthcare Payer & Clinical domain. The design draws on architectural prior art from [`gemini-ops-fleet`](https://github.com/sechan9999/gemini-ops-fleet) and [`unified-ops-ax`](https://github.com/sechan9999/unified-ops-ax).

---

## 📄 License
MIT License. Built for enterprise governance on Gemini + ADK.
