from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    PAYER_ADMIN = "payer_admin"
    CLAIMS_SPECIALIST = "claims_specialist"
    CLINICIAN = "clinician"
    GROWTH_LEAD = "growth_lead"
    MEDICAL_DIRECTOR = "medical_director"
    ANONYMOUS = "anonymous"


class DomainDomain(str, Enum):
    PAYER = "payer"
    CLINICAL = "clinical"
    CROSS_DOMAIN = "cross_domain"


class AutonomyGrade(str, Enum):
    AUTONOMOUS = "autonomous"
    DRAFTS_ONLY = "drafts_only"
    READ_ONLY = "read_only"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISPATCHED = "dispatched"


class UserIdentity(BaseModel):
    token: str
    user_id: str
    name: str
    role: UserRole
    department: str
    allowed_domains: List[DomainDomain]


class DocumentRecord(BaseModel):
    doc_id: str
    title: str
    domain: DomainDomain
    classification: str  # public, internal_payer, clinical_restricted, confidential_rates
    required_roles: List[UserRole]
    content: str
    summary: str
    cpt_codes: List[str] = Field(default_factory=list)
    icd10_codes: List[str] = Field(default_factory=list)
    effective_date: str = "2026-01-01"


class DenialRecord(BaseModel):
    claim_id: str
    patient_id_hash: str
    payer_name: str
    denial_code: str
    denial_reason: str
    appeal_deadline: str
    recommended_strategy: str
    required_roles: List[UserRole] = [UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.MEDICAL_DIRECTOR]


class CareGapRecord(BaseModel):
    gap_id: str
    patient_id_hash: str
    measure_name: str  # e.g., HEDIS-COL (Colorectal Screening), HbA1c Control
    clinical_priority: str  # High, Medium, Low
    recommended_action: str
    due_date: str
    required_roles: List[UserRole] = [UserRole.CLINICIAN, UserRole.GROWTH_LEAD, UserRole.MEDICAL_DIRECTOR]


class ApprovalItem(BaseModel):
    approval_id: str
    agent_id: str
    action_type: str  # e.g., PRIOR_AUTH_SUBMISSION, PATIENT_DISPATCH, PROTOCOL_UPDATE
    target_domain: DomainDomain
    summary: str
    payload: Dict
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


class AuditLogEntry(BaseModel):
    audit_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: str
    user_role: UserRole
    agent_id: str
    action: str
    domain: DomainDomain
    access_granted: bool
    denial_reason: Optional[str] = None
    query_summary: str
    documents_accessed: List[str] = Field(default_factory=list)
    guardrail_status: str = "PASS"


class ActivityEvent(BaseModel):
    event_id: str
    event_type: str  # e.g., POLICY_QUERIED, DENIAL_ANALYZED, CARE_GAP_IDENTIFIED, APPROVAL_QUEUED
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    domain: DomainDomain
    actor_role: UserRole
    details: Dict
