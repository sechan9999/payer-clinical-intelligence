from datetime import datetime
import json
import sqlite3
from typing import Dict, List, Optional
from app.config import get_database_urls
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
    """
    Unified Data Store supporting local SQLite storage and Cloud SQL PostgreSQL.
    Stores documents, denial records, care gaps, approval queue items, and audit logs.
    """

    def __init__(self, db_path: str = "fleet.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        if self.db_path == ":memory:":
            if not hasattr(self, "_mem_conn") or self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            return self._mem_conn
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                title TEXT,
                domain TEXT,
                classification TEXT,
                required_roles TEXT,
                content TEXT,
                summary TEXT,
                cpt_codes TEXT,
                icd10_codes TEXT,
                effective_date TEXT
            )
        """)

        # Denial records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS denial_records (
                claim_id TEXT PRIMARY KEY,
                patient_id_hash TEXT,
                payer_name TEXT,
                denial_code TEXT,
                denial_reason TEXT,
                appeal_deadline TEXT,
                recommended_strategy TEXT,
                required_roles TEXT
            )
        """)

        # Care gap records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS care_gaps (
                gap_id TEXT PRIMARY KEY,
                patient_id_hash TEXT,
                measure_name TEXT,
                clinical_priority TEXT,
                recommended_action TEXT,
                due_date TEXT,
                required_roles TEXT
            )
        """)

        # Approval items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_queue (
                approval_id TEXT PRIMARY KEY,
                agent_id TEXT,
                action_type TEXT,
                target_domain TEXT,
                summary TEXT,
                payload TEXT,
                status TEXT,
                created_at TEXT,
                approved_by TEXT,
                approved_at TEXT
            )
        """)

        # Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                audit_id TEXT PRIMARY KEY,
                timestamp TEXT,
                user_id TEXT,
                user_role TEXT,
                agent_id TEXT,
                action TEXT,
                domain TEXT,
                access_granted INTEGER,
                denial_reason TEXT,
                query_summary TEXT,
                documents_accessed TEXT,
                guardrail_status TEXT
            )
        """)

        # Activity events stream
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT,
                timestamp TEXT,
                domain TEXT,
                actor_role TEXT,
                details TEXT
            )
        """)

        conn.commit()

        # Seed mock database if empty
        cursor.execute("SELECT COUNT(*) FROM documents")
        if cursor.fetchone()[0] == 0:
            self._seed_mock_data(conn)

    def _seed_mock_data(self, conn):
        cursor = conn.cursor()

        docs = [
            DocumentRecord(
                doc_id="PAY-POL-101",
                title="Commercial Prior Auth Guidelines for Advanced Cardiac Imaging",
                domain=DomainDomain.PAYER,
                classification="internal_payer",
                required_roles=[UserRole.PAYER_ADMIN, UserRole.CLAIMS_SPECIALIST, UserRole.MEDICAL_DIRECTOR],
                content="Prior authorization for Cardiac MRI (CPT 75561) requires documented echocardiogram within 90 days demonstrating LVEF < 40% or inconclusive valvular assessment. Exclusions apply for acute STEMI.",
                summary="Cardiac MRI CPT 75561 prior authorization coverage criteria.",
                cpt_codes=["75561", "75562"],
                icd10_codes=["I42.0", "I50.9"],
            ),
            DocumentRecord(
                doc_id="PAY-RATE-202",
                title="Confidential Payer Fee Schedule & Contracted Rates 2026",
                domain=DomainDomain.PAYER,
                classification="confidential_rates",
                required_roles=[UserRole.PAYER_ADMIN, UserRole.MEDICAL_DIRECTOR],
                content="Confidential contracted rate table: CPT 75561 baseline reimbursement $1,420.00. CPT 93458 Coronary Angiography reimbursement $3,150.00. Rates restricted to Payer Executive Contracting.",
                summary="Confidential contracted reimbursement rates for cardiology procedures.",
                cpt_codes=["75561", "93458"],
                icd10_codes=[],
            ),
            DocumentRecord(
                doc_id="CLN-GUIDE-401",
                title="ACC/AHA Clinical Practice Guideline for Heart Failure Management",
                domain=DomainDomain.CLINICAL,
                classification="clinical_restricted",
                required_roles=[UserRole.CLINICIAN, UserRole.GROWTH_LEAD, UserRole.MEDICAL_DIRECTOR],
                content="Guideline-directed medical therapy (GDMT) for HFrEF includes ARNI/ACEi/ARB, beta-blocker, MRA, and SGLT2i. Cardiac MRI is recommended (Class 1, LOE B) for evaluating myocardial viability prior to revascularization.",
                summary="ACC/AHA Guideline recommendations for GDMT and myocardial viability imaging.",
                cpt_codes=["75561"],
                icd10_codes=["I50.22", "I50.9"],
            ),
            DocumentRecord(
                doc_id="CLN-GROWTH-502",
                title="Clinical Growth Initiative: Diabetes & Heart Failure Care Gap Protocol",
                domain=DomainDomain.CLINICAL,
                classification="clinical_restricted",
                required_roles=[UserRole.CLINICIAN, UserRole.GROWTH_LEAD, UserRole.MEDICAL_DIRECTOR],
                content="Population health outreach for HEDIS-HbA1c care gaps. Patients with HbA1c > 9.0% and concurrent HFrEF qualify for home SGLT2i medication titration and telehealth nurse navigation.",
                summary="Population health growth outreach protocol for HEDIS HbA1c & Heart Failure care gaps.",
                cpt_codes=[],
                icd10_codes=["E11.9", "I50.9"],
            ),
        ]

        for d in docs:
            cursor.execute(
                """INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    d.doc_id,
                    d.title,
                    d.domain.value,
                    d.classification,
                    json.dumps([r.value for r in d.required_roles]),
                    d.content,
                    d.summary,
                    json.dumps(d.cpt_codes),
                    json.dumps(d.icd10_codes),
                    d.effective_date,
                ),
            )

        # Seed sample denial
        denial = DenialRecord(
            claim_id="CLM-9921",
            patient_id_hash="hash_pt_8841",
            payer_name="Apex Health Plan",
            denial_code="CO-50",
            denial_reason="Non-covered procedure code / Lack of documented prior authorization",
            appeal_deadline="2026-09-30",
            recommended_strategy="Submit peer-to-peer review with prior Echocardiogram LVEF report referencing PAY-POL-101 section 3.",
        )
        cursor.execute(
            """INSERT INTO denial_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                denial.claim_id,
                denial.patient_id_hash,
                denial.payer_name,
                denial.denial_code,
                denial.denial_reason,
                denial.appeal_deadline,
                denial.recommended_strategy,
                json.dumps([r.value for r in denial.required_roles]),
            ),
        )

        conn.commit()

    def get_documents_by_roles(self, roles: List[UserRole]) -> List[DocumentRecord]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents")
        rows = cursor.fetchall()

        role_vals = [r.value for r in roles]
        permitted = []
        for r in rows:
            req_roles = json.loads(r[4])
            if any(role in req_roles for role in role_vals):
                permitted.append(
                    DocumentRecord(
                        doc_id=r[0],
                        title=r[1],
                        domain=DomainDomain(r[2]),
                        classification=r[3],
                        required_roles=[UserRole(role_str) for role_str in req_roles],
                        content=r[5],
                        summary=r[6],
                        cpt_codes=json.loads(r[7]),
                        icd10_codes=json.loads(r[8]),
                        effective_date=r[9],
                    )
                )
        return permitted

    def add_approval_item(self, item: ApprovalItem):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO approval_queue VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item.approval_id,
                item.agent_id,
                item.action_type,
                item.target_domain.value,
                item.summary,
                json.dumps(item.payload),
                item.status.value,
                item.created_at,
                item.approved_by,
                item.approved_at,
            ),
        )
        conn.commit()

    def get_approval_items(self, status: Optional[ApprovalStatus] = None) -> List[ApprovalItem]:
        conn = self._get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM approval_queue WHERE status = ?", (status.value,))
        else:
            cursor.execute("SELECT * FROM approval_queue")
        rows = cursor.fetchall()

        items = []
        for r in rows:
            items.append(
                ApprovalItem(
                    approval_id=r[0],
                    agent_id=r[1],
                    action_type=r[2],
                    target_domain=DomainDomain(r[3]),
                    summary=r[4],
                    payload=json.loads(r[5]),
                    status=ApprovalStatus(r[6]),
                    created_at=r[7],
                    approved_by=r[8],
                    approved_at=r[9],
                )
            )
        return items

    def update_approval_status(self, approval_id: str, new_status: ApprovalStatus, approved_by: str, approved_at: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE approval_queue SET status = ?, approved_by = ?, approved_at = ? WHERE approval_id = ?""",
            (new_status.value, approved_by, approved_at, approval_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def add_audit_log(self, entry: AuditLogEntry):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO audit_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.audit_id,
                entry.timestamp,
                entry.user_id,
                entry.user_role.value,
                entry.agent_id,
                entry.action,
                entry.domain.value,
                1 if entry.access_granted else 0,
                entry.denial_reason,
                entry.query_summary,
                json.dumps(entry.documents_accessed),
                entry.guardrail_status,
            ),
        )
        conn.commit()

    def get_audit_logs(self) -> List[AuditLogEntry]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        logs = []
        for r in rows:
            logs.append(
                AuditLogEntry(
                    audit_id=r[0],
                    timestamp=r[1],
                    user_id=r[2],
                    user_role=UserRole(r[3]),
                    agent_id=r[4],
                    action=r[5],
                    domain=DomainDomain(r[6]),
                    access_granted=bool(r[7]),
                    denial_reason=r[8],
                    query_summary=r[9],
                    documents_accessed=json.loads(r[10]),
                    guardrail_status=r[11],
                )
            )
        return logs

    def record_activity(self, event: ActivityEvent):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO activity_events VALUES (?, ?, ?, ?, ?, ?)""",
            (
                event.event_id,
                event.event_type,
                event.timestamp,
                event.domain.value,
                event.actor_role.value,
                json.dumps(event.details),
            ),
        )
        conn.commit()

    def get_activities(self) -> List[ActivityEvent]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM activity_events ORDER BY timestamp DESC")
        rows = cursor.fetchall()

        activities = []
        for r in rows:
            activities.append(
                ActivityEvent(
                    event_id=r[0],
                    event_type=r[1],
                    timestamp=r[2],
                    domain=DomainDomain(r[3]),
                    actor_role=UserRole(r[4]),
                    details=json.loads(r[5]),
                )
            )
        return activities


_GLOBAL_STORE: Optional[DataStore] = None


def get_store() -> DataStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = DataStore()
    return _GLOBAL_STORE
