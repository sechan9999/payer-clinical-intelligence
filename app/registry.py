from typing import Dict, List
from pydantic import BaseModel, Field
from app.domain import AutonomyGrade, DomainDomain, UserRole


class AgentMetadata(BaseModel):
    agent_id: str
    name: str
    version: str
    description: str
    primary_domain: DomainDomain
    autonomy_grade: AutonomyGrade
    allowed_roles: List[UserRole]
    tools: List[str]
    restrictions: List[str]


AGENT_REGISTRY: Dict[str, AgentMetadata] = {
    "payer_intelligence": AgentMetadata(
        agent_id="payer_intelligence",
        name="Payer Intelligence Agent",
        version="1.2.0",
        description="Analyzes payer coverage rules, CPT/ICD-10 coding criteria, fee schedules, prior auth requirements, and claim denial appeal strategies.",
        primary_domain=DomainDomain.PAYER,
        autonomy_grade=AutonomyGrade.DRAFTS_ONLY,
        allowed_roles=[UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.MEDICAL_DIRECTOR],
        tools=[
            "query_payer_policies",
            "analyze_denial_reasons",
            "verify_coverage_eligibility",
            "queue_prior_auth_request",
        ],
        restrictions=[
            "Cannot access raw patient clinical charts without explicit medical director role.",
            "Cannot send unapproved prior authorization requests directly to external payers.",
            "Cannot widen own role permissions.",
            "Autonomy grade is strictly 'drafts_only'; zero send or dispatch tools permitted.",
        ],
    ),
    "clinical_growth": AgentMetadata(
        agent_id="clinical_growth",
        name="Clinical & Growth Intelligence Agent",
        version="1.2.0",
        description="Analyzes ACC/AHA clinical guidelines, quality care gaps (HEDIS/mIPS), care pathways, and clinical growth/outreach initiatives.",
        primary_domain=DomainDomain.CLINICAL,
        autonomy_grade=AutonomyGrade.DRAFTS_ONLY,
        allowed_roles=[UserRole.CLINICIAN, UserRole.GROWTH_LEAD, UserRole.MEDICAL_DIRECTOR],
        tools=[
            "query_clinical_guidelines",
            "evaluate_care_gaps",
            "summarize_clinical_history",
            "queue_growth_initiative",
        ],
        restrictions=[
            "Cannot access confidential Payer fee schedules or contracted rate sheets.",
            "Cannot dispatch care plan communications to patients without human supervisor approval.",
            "Cannot provide diagnostic advice without document citations.",
            "Autonomy grade is strictly 'drafts_only'; zero send or dispatch tools permitted.",
        ],
    ),
    "coordinator": AgentMetadata(
        agent_id="coordinator",
        name="Fleet Coordinator Agent",
        version="1.0.0",
        description="Orchestrates requests across Payer and Clinical agents, enforcing cross-domain role boundary checks.",
        primary_domain=DomainDomain.CROSS_DOMAIN,
        autonomy_grade=AutonomyGrade.READ_ONLY,
        allowed_roles=[UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.CLINICIAN, UserRole.GROWTH_LEAD, UserRole.MEDICAL_DIRECTOR],
        tools=["route_query"],
        restrictions=[
            "Delegates to domain agents while passing down server-derived user identity.",
            "Autonomy grade is strictly 'read_only'; orchestration and intent routing only.",
        ],
    ),
}


def get_agent_registry() -> List[AgentMetadata]:
    return list(AGENT_REGISTRY.values())


def get_agent_metadata(agent_id: str) -> AgentMetadata:
    if agent_id not in AGENT_REGISTRY:
        raise KeyError(f"Agent ID '{agent_id}' not found in registry.")
    return AGENT_REGISTRY[agent_id]
