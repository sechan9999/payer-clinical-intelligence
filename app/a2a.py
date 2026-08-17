from typing import Dict, List
from app.config import check_runtime_environment
from app.registry import get_agent_registry


def generate_agent_card() -> Dict:
    """
    Generates A2A Protocol Agent Card JSON metadata for A2A Inspector interoperability.
    Reflects dynamic runtime environment and GCP status transparently.
    """
    agents = get_agent_registry()
    runtime = check_runtime_environment()
    
    skills = []
    for a in agents:
        for t in a.tools:
            skills.append({
                "id": t,
                "name": t.replace("_", " ").title(),
                "description": f"Tool capability provided by {a.name}",
                "agent_owner": a.agent_id,
                "domain": a.primary_domain.value,
                "autonomy_grade": a.autonomy_grade.value,
            })

    return {
        "name": "Payer Clinical Intelligence Fleet",
        "description": "Governed multi-agent back-office fleet on Gemini + ADK over an auditable RAG layer",
        "version": "0.1.0",
        "protocol_version": "0.2.0",
        "runtime_status": runtime,
        "capabilities": {
            "a2a_communication": True,
            "extractive_rag": True,
            "sql_rbac_isolation": True,
            "human_in_the_loop_gate": True,
            "opentelemetry_tracing": True,
            "vertex_ai_model_active": runtime["has_gcp_credentials"],
        },
        "agents": [a.model_dump() for a in agents],
        "skills": skills,
        "governance_contract": {
            "identity_derivation": "server_side_bearer_and_x_fleet_token_header",
            "model_armor_status": runtime["model_armor_status"],
            "database_backend": runtime["database_backend"],
            "audit_trail": "append_only_sqlite_cloudsql",
        }
    }
