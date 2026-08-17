import json
import sqlite3
import uuid
from typing import Dict, List, Optional, Tuple
from app.domain import (
    ActivityEvent,
    ApprovalItem,
    ApprovalStatus,
    AuditLogEntry,
    CareGapRecord,
    DenialRecord,
    DocumentRecord,
    DomainDomain,
    UserRole,
)


class DataStore:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self._seed_data()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    required_roles TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    cpt_codes TEXT,
                    icd10_codes TEXT,
                    effective_date TEXT
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS denials (
                    claim_id TEXT PRIMARY KEY,
                    patient_id_hash TEXT NOT NULL,
                    payer_name TEXT NOT NULL,
                    denial_code TEXT NOT NULL,
                    denial_reason TEXT NOT NULL,
                    appeal_deadline TEXT NOT NULL,
                    recommended_strategy TEXT NOT NULL,
                    required_roles TEXT NOT NULL
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS care_gaps (
                    gap_id TEXT PRIMARY KEY,
                    patient_id_hash TEXT NOT NULL,
                    measure_name TEXT NOT NULL,
                    clinical_priority TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    required_roles TEXT NOT NULL
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_domain TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_role TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    access_granted INTEGER NOT NULL,
                    denial_reason TEXT,
                    query_summary TEXT NOT NULL,
                    documents_accessed TEXT NOT NULL,
                    guardrail_status TEXT NOT NULL
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    actor_role TEXT NOT NULL,
                    details TEXT NOT NULL
                );
            """)

    def _seed_data(self):
        # Check if already seeded
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        if cursor.fetchone()[0] > 0:
            return

        documents = [
            # Payer Policies
            DocumentRecord(
                doc_id="PAY-POL-101",
                title="Commercial Prior Authorization Policy for Cardiac MRI",
                domain=DomainDomain.PAYER,
                classification="internal_payer",
                required_roles=[UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.MEDICAL_DIRECTOR],
                content="Prior authorization for Cardiac MRI (CPT 75561) requires documentation of inconclusive Echocardiogram (CPT 93306), symptoms of cardiomyopathy, or suspect myocardial ischemia. Pre-certification valid for 60 days.",
                summary="Cardiac MRI prior auth rules: requires non-diagnostic Echo, specific ICD-10 I42.0.",
                cpt_codes=["75561", "93306"],
                icd10_codes=["I42.0", "I50.9"],
            ),
            DocumentRecord(
                doc_id="PAY-RATE-202",
                title="Confidential Payer Fee Schedule & Contracted Rates 2026",
                domain=DomainDomain.PAYER,
                classification="confidential_rates",
                required_roles=[UserRole.PAYER_ADMIN, UserRole.MEDICAL_DIRECTOR],
                content="CONFIDENTIAL: Tier 1 Network reimbursement for Cardiac MRI (75561) set at $1,450. Out-of-network allowable capped at 140% of CMS Medicare base rate ($580). Shared savings target: 5% reduction in unapproved outpatient imaging.",
                summary="Confidential Payer fee schedule for 75561 ($1,450 contracted rate). Restrict to Payer Admin.",
                cpt_codes=["75561"],
                icd10_codes=[],
            ),
            DocumentRecord(
                doc_id="PAY-DEN-303",
                title="Medicare Advantage Claim Denial Resolution Guide",
                domain=DomainDomain.PAYER,
                classification="internal_payer",
                required_roles=[UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.MEDICAL_DIRECTOR],
                content="Denial Code CO-50 (Non-covered medical necessity): Appeal must include Physician Attestation within 30 calendar days. Denial Code OA-197 (Pre-cert missing): Retroactive auth allowed only if emergent.",
                summary="Denial code CO-50 and OA-197 resolution steps and appeal deadlines.",
                cpt_codes=[],
                icd10_codes=[],
            ),
            # Clinical Guidelines
            DocumentRecord(
                doc_id="CLN-GUIDE-401",
                title="ACC/AHA Clinical Practice Guideline for Heart Failure Management",
                domain=DomainDomain.CLINICAL,
                classification="clinical_restricted",
                required_roles=[UserRole.CLINICIAN, UserRole.GROWTH_LEAD, UserRole.MEDICAL_DIRECTOR],
                content="Class I Recommendation: Patients with HFrEF (LVEF <= 40%) should receive GDMT including SGLT2 inhibitors, ARNI/ACEi, Beta-Blockers, and MRAs to reduce mortality and hospitalization risk.",
                summary="Clinical HF guidelines: GDMT quartet regimen for LVEF <= 40%.",
                cpt_codes=["99214", "99215"],
                icd10_codes=["I50.22", "I50.42"],
            ),
            DocumentRecord(
                doc_id="CLN-GROWTH-502",
                title="Clinical Care Gap & Service Line Growth Playbook 2026",
                domain=DomainDomain.CLINICAL,
                classification="clinical_restricted",
                required_roles=[UserRole.GROWTH_LEAD, UserRole.CLINICIAN, UserRole.MEDICAL_DIRECTOR],
                content="Growth Opportunity: 32% of patients with Type 2 Diabetes (E11.9) lack annual HbA1c screening or Nephropathy screening (CPT 83036). Outreach campaign expected to improve HEDIS score from 3 stars to 4.5 stars.",
                summary="Quality care gap strategy for Diabetes screening and HEDIS rating boost.",
                cpt_codes=["83036", "82570"],
                icd10_codes=["E11.9"],
            ),
        ]

        with self.conn:
            for doc in documents:
                self.conn.execute("""
                    INSERT INTO documents (doc_id, title, domain, classification, required_roles, content, summary, cpt_codes, icd10_codes, effective_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.doc_id, doc.title, doc.domain.value, doc.classification,
                    json.dumps([r.value for r in doc.required_roles]),
                    doc.content, doc.summary, json.dumps(doc.cpt_codes),
                    json.dumps(doc.icd10_codes), doc.effective_date
                ))

            # Seed Denials
            self.conn.execute("""
                INSERT INTO denials (claim_id, patient_id_hash, payer_name, denial_code, denial_reason, appeal_deadline, recommended_strategy, required_roles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "CLM-9921", "hash_pt_8821", "Aetna Health", "CO-50",
                "Lack of Medical Necessity documentation for CPT 75561", "2026-09-15",
                "Submit Echocardiogram report showing EF=35% and Attestation of failure on Echo",
                json.dumps([UserRole.PAYER_ADMIN.value, UserRole.CLAIMS_SPECIALIST.value, UserRole.MEDICAL_DIRECTOR.value])
            ))

            # Seed Care Gaps
            self.conn.execute("""
                INSERT INTO care_gaps (gap_id, patient_id_hash, measure_name, clinical_priority, recommended_action, due_date, required_roles)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "GAP-4401", "hash_pt_3312", "HEDIS-HbA1c-Control", "High",
                "Order HbA1c lab kit and schedule Nurse Practitioner Telehealth Consult", "2026-08-30",
                json.dumps([UserRole.CLINICIAN.value, UserRole.GROWTH_LEAD.value, UserRole.MEDICAL_DIRECTOR.value])
            ))

    def get_documents_by_roles(self, allowed_roles: List[UserRole], domain_filter: Optional[DomainDomain] = None) -> List[DocumentRecord]:
        role_strings = set(r.value for r in allowed_roles)
        cursor = self.conn.cursor()
        
        if domain_filter:
            cursor.execute("SELECT * FROM documents WHERE domain = ?", (domain_filter.value,))
        else:
            cursor.execute("SELECT * FROM documents")

        results = []
        for row in cursor.fetchall():
            required_roles = set(json.loads(row["required_roles"]))
            # Check if user's roles intersect with document's required roles
            if required_roles.intersection(role_strings):
                results.append(DocumentRecord(
                    doc_id=row["doc_id"],
                    title=row["title"],
                    domain=DomainDomain(row["domain"]),
                    classification=row["classification"],
                    required_roles=[UserRole(r) for r in json.loads(row["required_roles"])],
                    content=row["content"],
                    summary=row["summary"],
                    cpt_codes=json.loads(row["cpt_codes"]),
                    icd10_codes=json.loads(row["icd10_codes"]),
                    effective_date=row["effective_date"]
                ))
        return results

    def add_approval_item(self, item: ApprovalItem):
        with self.conn:
            self.conn.execute("""
                INSERT INTO approvals (approval_id, agent_id, action_type, target_domain, summary, payload, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.approval_id, item.agent_id, item.action_type,
                item.target_domain.value, item.summary, json.dumps(item.payload),
                item.status.value, item.created_at
            ))

    def get_approval_items(self, status: Optional[ApprovalStatus] = None) -> List[ApprovalItem]:
        cursor = self.conn.cursor()
        if status:
            cursor.execute("SELECT * FROM approvals WHERE status = ?", (status.value,))
        else:
            cursor.execute("SELECT * FROM approvals")
        
        items = []
        for row in cursor.fetchall():
            items.append(ApprovalItem(
                approval_id=row["approval_id"],
                agent_id=row["agent_id"],
                action_type=row["action_type"],
                target_domain=DomainDomain(row["target_domain"]),
                summary=row["summary"],
                payload=json.loads(row["payload"]),
                status=ApprovalStatus(row["status"]),
                created_at=row["created_at"],
                approved_by=row["approved_by"],
                approved_at=row["approved_at"]
            ))
        return items

    def update_approval_status(self, approval_id: str, status: ApprovalStatus, approved_by: str, timestamp: str) -> bool:
        with self.conn:
            cursor = self.conn.execute("""
                UPDATE approvals
                SET status = ?, approved_by = ?, approved_at = ?
                WHERE approval_id = ?
            """, (status.value, approved_by, timestamp, approval_id))
            return cursor.rowcount > 0

    def add_audit_log(self, entry: AuditLogEntry):
        with self.conn:
            self.conn.execute("""
                INSERT INTO audit_logs (audit_id, timestamp, user_id, user_role, agent_id, action, domain, access_granted, denial_reason, query_summary, documents_accessed, guardrail_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.audit_id, entry.timestamp, entry.user_id, entry.user_role.value,
                entry.agent_id, entry.action, entry.domain.value,
                1 if entry.access_granted else 0, entry.denial_reason,
                entry.query_summary, json.dumps(entry.documents_accessed), entry.guardrail_status
            ))

    def get_audit_logs(self) -> List[AuditLogEntry]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
        logs = []
        for row in cursor.fetchall():
            logs.append(AuditLogEntry(
                audit_id=row["audit_id"],
                timestamp=row["timestamp"],
                user_id=row["user_id"],
                user_role=UserRole(row["user_role"]),
                agent_id=row["agent_id"],
                action=row["action"],
                domain=DomainDomain(row["domain"]),
                access_granted=bool(row["access_granted"]),
                denial_reason=row["denial_reason"],
                query_summary=row["query_summary"],
                documents_accessed=json.loads(row["documents_accessed"]),
                guardrail_status=row["guardrail_status"]
            ))
        return logs

    def record_activity(self, event: ActivityEvent):
        with self.conn:
            self.conn.execute("""
                INSERT INTO activities (event_id, event_type, timestamp, domain, actor_role, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.event_type, event.timestamp,
                event.domain.value, event.actor_role.value, json.dumps(event.details)
            ))

    def get_activities(self) -> List[ActivityEvent]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM activities ORDER BY timestamp DESC")
        events = []
        for row in cursor.fetchall():
            events.append(ActivityEvent(
                event_id=row["event_id"],
                event_type=row["event_type"],
                timestamp=row["timestamp"],
                domain=DomainDomain(row["domain"]),
                actor_role=UserRole(row["actor_role"]),
                details=json.loads(row["details"])
            ))
        return events


# Global singleton instance for local runtime
_store_instance: Optional[DataStore] = None

def get_store() -> DataStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = DataStore()
    return _store_instance
