from typing import Dict, List, Optional
from app.domain import DomainDomain, UserIdentity, UserRole
from app.guardrails import validate_input_query, validate_output_response
from app.registry import get_agent_metadata
from app.tools import (
    analyze_denial_reasons,
    evaluate_care_gaps,
    query_clinical_guidelines,
    query_payer_policies,
    queue_growth_initiative,
    queue_prior_auth_request,
    summarize_clinical_history,
    verify_coverage_eligibility,
)


class PayerIntelligenceAgent:
    def __init__(self):
        self.metadata = get_agent_metadata("payer_intelligence")

    def process(self, query: str, user_identity: UserIdentity, action_type: Optional[str] = None, params: Optional[dict] = None) -> Dict:
        params = params or {}
        
        # Action dispatch
        if action_type == "analyze_denial":
            return analyze_denial_reasons(params.get("claim_id", "CLM-9921"), user_identity)
        elif action_type == "verify_coverage":
            return verify_coverage_eligibility(params.get("cpt_code", "75561"), params.get("icd10_code", "I42.0"), user_identity)
        elif action_type == "queue_prior_auth":
            return queue_prior_auth_request(
                params.get("cpt_code", "75561"),
                params.get("icd10_code", "I42.0"),
                params.get("clinical_rationale", "Patient exhibits symptoms of cardiomyopathy"),
                user_identity
            )
        
        # Default policy query
        result = query_payer_policies(query, user_identity)
        if not result["success"]:
            return {
                "agent_id": self.metadata.agent_id,
                "status": "DENIED",
                "response": f"Access Denied: {result['error']}",
                "citation_ids": [],
            }

        citations = result["citation_ids"]
        doc_summaries = "\n".join([f"- [{d['doc_id']}] {d['title']}: {d['summary']}" for d in result["documents"]])
        
        response_text = f"Payer Policy Analysis:\n{doc_summaries}\n\nCitations: {', '.join(citations)}"
        return {
            "agent_id": self.metadata.agent_id,
            "status": "SUCCESS",
            "response": response_text,
            "citation_ids": citations,
            "raw_data": result,
        }


class ClinicalGrowthAgent:
    def __init__(self):
        self.metadata = get_agent_metadata("clinical_growth")

    def process(self, query: str, user_identity: UserIdentity, action_type: Optional[str] = None, params: Optional[dict] = None) -> Dict:
        params = params or {}

        if action_type == "evaluate_care_gaps":
            return evaluate_care_gaps(params.get("measure_filter", "HEDIS-HbA1c"), user_identity)
        elif action_type == "summarize_clinical_history":
            return summarize_clinical_history(params.get("patient_id_hash", "hash_pt_3312"), user_identity)
        elif action_type == "queue_growth_initiative":
            return queue_growth_initiative(
                params.get("initiative_name", "Diabetes Quality Outreach 2026"),
                params.get("target_cohort", "Type 2 Diabetes non-compliant"),
                params.get("clinical_protocol", "HbA1c Nurse Telehealth Consult"),
                user_identity
            )

        # Default clinical guideline query
        result = query_clinical_guidelines(query, user_identity)
        if not result["success"]:
            return {
                "agent_id": self.metadata.agent_id,
                "status": "DENIED",
                "response": f"Access Denied: {result['error']}",
                "citation_ids": [],
            }

        citations = result["citation_ids"]
        doc_summaries = "\n".join([f"- [{d['doc_id']}] {d['title']}: {d['summary']}" for d in result["documents"]])
        
        response_text = f"Clinical Practice Guidance:\n{doc_summaries}\n\nCitations: {', '.join(citations)}"
        return {
            "agent_id": self.metadata.agent_id,
            "status": "SUCCESS",
            "response": response_text,
            "citation_ids": citations,
            "raw_data": result,
        }


class FleetCoordinator:
    def __init__(self):
        self.payer_agent = PayerIntelligenceAgent()
        self.clinical_agent = ClinicalGrowthAgent()

    def route_and_execute(
        self,
        query: str,
        user_identity: UserIdentity,
        target_domain: Optional[DomainDomain] = None,
        action_type: Optional[str] = None,
        params: Optional[dict] = None
    ) -> Dict:
        # Step 1: Input Guardrail Check
        is_safe, guard_reason = validate_input_query(query)
        if not is_safe:
            return {
                "coordinator_status": "BLOCKED_GUARDRAIL",
                "guardrail_reason": guard_reason,
                "response": f"Query blocked by safety guardrails: {guard_reason}",
                "citation_ids": [],
            }

        # Step 2: Route based on domain or query intent
        query_lower = query.lower()
        if target_domain == DomainDomain.PAYER or "cpt" in query_lower or "payer" in query_lower or "denial" in query_lower or "prior auth" in query_lower or "fee" in query_lower:
            agent_result = self.payer_agent.process(query, user_identity, action_type, params)
        elif target_domain == DomainDomain.CLINICAL or "guideline" in query_lower or "care gap" in query_lower or "clinical" in query_lower or "hedis" in query_lower:
            agent_result = self.clinical_agent.process(query, user_identity, action_type, params)
        else:
            # Fallback cross-domain routing based on user's primary domain
            if DomainDomain.PAYER in user_identity.allowed_domains:
                agent_result = self.payer_agent.process(query, user_identity, action_type, params)
            else:
                agent_result = self.clinical_agent.process(query, user_identity, action_type, params)

        # Step 3: Response Guardrail Validation
        if agent_result.get("status") == "SUCCESS":
            citations = agent_result.get("citation_ids", [])
            val_ok, val_note = validate_output_response(agent_result.get("response", ""), citations)
            agent_result["guardrail_output_validation"] = val_note

        return {
            "coordinator_status": "COMPLETED",
            "user_role": user_identity.role.value,
            "result": agent_result,
        }
