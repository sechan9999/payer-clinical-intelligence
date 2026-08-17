import logging
import os
from typing import Dict, List, Optional, Tuple
from app.config import check_runtime_environment
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

logger = logging.getLogger("payer_clinical_fleet")

# Import google-genai SDK if available
try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


def call_gemini_inference(
    prompt: str,
    system_instruction: str,
    context_documents: List[Dict],
    model_name: str = "gemini-3.5-flash"
) -> Tuple[Optional[str], str]:
    """
    Executes real LLM inference via Gemini 3.5 Flash using google.genai SDK Client.
    Returns (generated_text, provider_status).
    If GCP credentials/API keys are missing, falls back gracefully to extractive synthesis.
    """
    runtime = check_runtime_environment()
    if not HAS_GENAI_SDK or not runtime["has_gcp_credentials"]:
        return None, "offline_extractive_fallback"

    try:
        # Initialize GenAI Client for Vertex AI / Gemini API
        gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        if gcp_project:
            client = genai.Client(vertexai=True, project=gcp_project, location=location)
        else:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        doc_context_str = "\n\n".join([
            f"Document ID: [{d['doc_id']}]\nTitle: {d['title']}\nContent: {d['content']}\nSummary: {d['summary']}"
            for d in context_documents
        ])

        full_prompt = (
            f"User Query: {prompt}\n\n"
            f"Retrieved Permitted Context Documents:\n{doc_context_str}\n\n"
            f"Instructions: Synthesize a concise, accurate answer based strictly on the retrieved context documents above. "
            f"You MUST explicitly cite the relevant Document IDs (e.g. [PAY-POL-101]) in your answer."
        )

        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
                max_output_tokens=1024,
            )
        )
        return response.text, f"gemini_3.5_flash_vertex ({gcp_project or 'api_key'})"
    except Exception as ex:
        logger.warning(f"Gemini API invocation failed ({type(ex).__name__}): {ex}. Falling back to extractive RAG.")
        return None, f"error_fallback_{type(ex).__name__}"


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
        docs = result["documents"]
        
        # Attempt Gemini 3.5 Flash Inference
        sys_inst = "You are the Payer Intelligence Agent. Answer using permitted coverage policies and cite Document IDs."
        gemini_text, provider_status = call_gemini_inference(query, sys_inst, docs)

        if gemini_text:
            response_text = f"Payer Policy Analysis (Gemini 3.5 Flash):\n{gemini_text}\n\nCitations: {', '.join(citations)}"
        else:
            doc_summaries = "\n".join([f"- [{d['doc_id']}] {d['title']}: {d['summary']}" for d in docs])
            response_text = f"Payer Policy Analysis (Extractive Grounded RAG):\n{doc_summaries}\n\nCitations: {', '.join(citations)}"

        return {
            "agent_id": self.metadata.agent_id,
            "status": "SUCCESS",
            "model_provider": provider_status,
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
        docs = result["documents"]

        # Attempt Gemini 3.5 Flash Inference
        sys_inst = "You are the Clinical & Growth Agent. Answer using permitted clinical guidelines and cite Document IDs."
        gemini_text, provider_status = call_gemini_inference(query, sys_inst, docs)

        if gemini_text:
            response_text = f"Clinical Practice Guidance (Gemini 3.5 Flash):\n{gemini_text}\n\nCitations: {', '.join(citations)}"
        else:
            doc_summaries = "\n".join([f"- [{d['doc_id']}] {d['title']}: {d['summary']}" for d in docs])
            response_text = f"Clinical Practice Guidance (Extractive Grounded RAG):\n{doc_summaries}\n\nCitations: {', '.join(citations)}"

        return {
            "agent_id": self.metadata.agent_id,
            "status": "SUCCESS",
            "model_provider": provider_status,
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
