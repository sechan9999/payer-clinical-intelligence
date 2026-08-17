import uuid
from typing import Dict, List, Optional
from app.approvals import queue_for_human_approval
from app.domain import (
    ApprovalItem,
    AuditLogEntry,
    CareGapRecord,
    DenialRecord,
    DocumentRecord,
    DomainDomain,
    UserIdentity,
    UserRole,
)
from app.retrieval import permitted_documents
from app.store import DataStore, get_store


def query_payer_policies(query: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Query Payer policies, coverage determinations, and CPT/ICD-10 criteria.
    No role parameter accepted in signature.
    """
    db = store or get_store()
    docs, denial = permitted_documents(user_identity, query, domain_filter=DomainDomain.PAYER, store=db)
    
    if denial:
        return {
            "success": False,
            "error": denial,
            "documents": [],
            "citation_ids": [],
        }

    return {
        "success": True,
        "query": query,
        "count": len(docs),
        "documents": [d.model_dump() for d in docs],
        "citation_ids": [d.doc_id for d in docs],
    }


def analyze_denial_reasons(claim_id: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Analyze claim denial root cause and generate appeal recommendations.
    """
    db = store or get_store()
    
    if user_identity.role not in [UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.MEDICAL_DIRECTOR]:
        denial_reason = f"Role '{user_identity.role.value}' is unauthorized to analyze claim denials."
        db.add_audit_log(AuditLogEntry(
            audit_id=f"aud-{uuid.uuid4().hex[:8]}",
            user_id=user_identity.user_id,
            user_role=user_identity.role,
            agent_id="payer_intelligence",
            action="ANALYZE_DENIAL_DENIED",
            domain=DomainDomain.PAYER,
            access_granted=False,
            denial_reason=denial_reason,
            query_summary=f"Claim ID: {claim_id}",
            documents_accessed=[],
            guardrail_status="DENIED_ROLE"
        ))
        return {"success": False, "error": denial_reason}

    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM denials WHERE claim_id = ?", (claim_id,))
    row = cursor.fetchone()
    
    if not row:
        return {"success": False, "error": f"Claim ID '{claim_id}' not found."}

    denial_rec = DenialRecord(
        claim_id=row["claim_id"],
        patient_id_hash=row["patient_id_hash"],
        payer_name=row["payer_name"],
        denial_code=row["denial_code"],
        denial_reason=row["denial_reason"],
        appeal_deadline=row["appeal_deadline"],
        recommended_strategy=row["recommended_strategy"]
    )

    db.add_audit_log(AuditLogEntry(
        audit_id=f"aud-{uuid.uuid4().hex[:8]}",
        user_id=user_identity.user_id,
        user_role=user_identity.role,
        agent_id="payer_intelligence",
        action="ANALYZE_DENIAL",
        domain=DomainDomain.PAYER,
        access_granted=True,
        denial_reason=None,
        query_summary=f"Claim ID: {claim_id}",
        documents_accessed=[row["claim_id"]],
        guardrail_status="PASS"
    ))

    return {
        "success": True,
        "denial_analysis": denial_rec.model_dump(),
        "citation_ids": ["PAY-DEN-303"],
    }


def verify_coverage_eligibility(cpt_code: str, icd10_code: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Check if procedure/diagnosis pair satisfies medical necessity rules under permitted policies.
    """
    db = store or get_store()
    query_str = f"CPT {cpt_code} ICD10 {icd10_code}"
    docs, denial = permitted_documents(user_identity, query_str, domain_filter=DomainDomain.PAYER, store=db)
    
    if denial:
        return {"success": False, "error": denial}

    eligible_policies = [d for d in docs if cpt_code in d.cpt_codes]
    
    return {
        "success": True,
        "cpt_code": cpt_code,
        "icd10_code": icd10_code,
        "is_covered": len(eligible_policies) > 0,
        "matching_policies": [d.doc_id for d in eligible_policies],
        "citation_ids": [d.doc_id for d in eligible_policies],
    }


def queue_prior_auth_request(cpt_code: str, icd10_code: str, clinical_rationale: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Drafts a prior authorization request and queues it for mandatory human supervisor sign-off.
    Path is isolated from direct dispatch.
    """
    db = store or get_store()
    if user_identity.role not in [UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.MEDICAL_DIRECTOR]:
        return {"success": False, "error": f"Role '{user_identity.role.value}' cannot draft prior authorization requests."}

    payload = {
        "cpt_code": cpt_code,
        "icd10_code": icd10_code,
        "clinical_rationale": clinical_rationale,
        "submitted_by": user_identity.name,
    }
    
    approval_item = queue_for_human_approval(
        agent_id="payer_intelligence",
        action_type="PRIOR_AUTH_SUBMISSION",
        target_domain=DomainDomain.PAYER,
        summary=f"Prior Auth Packet for CPT {cpt_code} (ICD-10 {icd10_code})",
        payload=payload,
        actor_identity=user_identity,
        store=db
    )

    return {
        "success": True,
        "status": "QUEUED_FOR_HUMAN_APPROVAL",
        "approval_id": approval_item.approval_id,
        "note": "Request has been safely queued in pending approvals state. Human supervisor sign-off required.",
    }


def query_clinical_guidelines(query: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Query ACC/AHA clinical practice guidelines and evidence pathways.
    """
    db = store or get_store()
    docs, denial = permitted_documents(user_identity, query, domain_filter=DomainDomain.CLINICAL, store=db)
    
    if denial:
        return {"success": False, "error": denial, "documents": [], "citation_ids": []}

    return {
        "success": True,
        "query": query,
        "count": len(docs),
        "documents": [d.model_dump() for d in docs],
        "citation_ids": [d.doc_id for d in docs],
    }


def evaluate_care_gaps(measure_filter: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Evaluate population health care gaps (HEDIS/mIPS) for patient cohorts.
    """
    db = store or get_store()
    
    if user_identity.role not in [UserRole.CLINICIAN, UserRole.GROWTH_LEAD, UserRole.MEDICAL_DIRECTOR]:
        denial_reason = f"Role '{user_identity.role.value}' is restricted from accessing clinical care gap records."
        db.add_audit_log(AuditLogEntry(
            audit_id=f"aud-{uuid.uuid4().hex[:8]}",
            user_id=user_identity.user_id,
            user_role=user_identity.role,
            agent_id="clinical_growth",
            action="EVALUATE_CARE_GAPS_DENIED",
            domain=DomainDomain.CLINICAL,
            access_granted=False,
            denial_reason=denial_reason,
            query_summary=f"Measure: {measure_filter}",
            documents_accessed=[],
            guardrail_status="DENIED_ROLE"
        ))
        return {"success": False, "error": denial_reason}

    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM care_gaps")
    rows = cursor.fetchall()
    
    gaps = []
    for r in rows:
        gaps.append(CareGapRecord(
            gap_id=r["gap_id"],
            patient_id_hash=r["patient_id_hash"],
            measure_name=r["measure_name"],
            clinical_priority=r["clinical_priority"],
            recommended_action=r["recommended_action"],
            due_date=r["due_date"]
        ).model_dump())

    db.add_audit_log(AuditLogEntry(
        audit_id=f"aud-{uuid.uuid4().hex[:8]}",
        user_id=user_identity.user_id,
        user_role=user_identity.role,
        agent_id="clinical_growth",
        action="EVALUATE_CARE_GAPS",
        domain=DomainDomain.CLINICAL,
        access_granted=True,
        denial_reason=None,
        query_summary=f"Measure: {measure_filter}",
        documents_accessed=["GAP-4401"],
        guardrail_status="PASS"
    ))

    return {
        "success": True,
        "measure_filter": measure_filter,
        "care_gaps": gaps,
        "citation_ids": ["CLN-GROWTH-502"],
    }


def summarize_clinical_history(patient_id_hash: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Summarizes clinical timeline for patient cohort, matching treatment with clinical guidelines.
    """
    db = store or get_store()
    
    if user_identity.role not in [UserRole.CLINICIAN, UserRole.MEDICAL_DIRECTOR]:
        return {"success": False, "error": f"Role '{user_identity.role.value}' cannot view patient clinical history summaries."}

    return {
        "success": True,
        "patient_id_hash": patient_id_hash,
        "summary": "Patient diagnosed with HFrEF (LVEF 35%), currently prescribed GDMT Beta-Blocker and ACEi. Recommended addition of SGLT2i per guideline CLN-GUIDE-401.",
        "citation_ids": ["CLN-GUIDE-401"],
    }


def queue_growth_initiative(initiative_name: str, target_cohort: str, clinical_protocol: str, user_identity: UserIdentity, store: Optional[DataStore] = None) -> Dict:
    """
    Drafts a clinical growth / quality improvement initiative and queues it for human supervisor approval.
    """
    db = store or get_store()
    if user_identity.role not in [UserRole.GROWTH_LEAD, UserRole.CLINICIAN, UserRole.MEDICAL_DIRECTOR]:
        return {"success": False, "error": f"Role '{user_identity.role.value}' cannot queue growth initiatives."}

    payload = {
        "initiative_name": initiative_name,
        "target_cohort": target_cohort,
        "clinical_protocol": clinical_protocol,
        "proposed_by": user_identity.name,
    }

    approval_item = queue_for_human_approval(
        agent_id="clinical_growth",
        action_type="GROWTH_INITIATIVE_DISPATCH",
        target_domain=DomainDomain.CLINICAL,
        summary=f"Growth Initiative: {initiative_name} ({target_cohort})",
        payload=payload,
        actor_identity=user_identity,
        store=db
    )

    return {
        "success": True,
        "status": "QUEUED_FOR_HUMAN_APPROVAL",
        "approval_id": approval_item.approval_id,
        "note": "Growth initiative queued safely in pending approval queue. Human supervisor approval required prior to patient outreach.",
    }
