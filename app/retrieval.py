import uuid
from typing import List, Optional, Tuple
from app.domain import AuditLogEntry, DocumentRecord, DomainDomain, UserIdentity, UserRole
from app.store import DataStore, get_store


def permitted_documents(
    identity: UserIdentity,
    query: str,
    domain_filter: Optional[DomainDomain] = None,
    store: Optional[DataStore] = None,
) -> Tuple[List[DocumentRecord], Optional[str]]:
    """
    SQL-level pre-retrieval role security filter.
    Restricts candidate query space by server-derived user role BEFORE semantic ranking.
    Returns (permitted_documents, denial_reason).
    """
    db = store or get_store()
    
    # Check domain access level
    if domain_filter and domain_filter not in identity.allowed_domains and identity.role != UserRole.MEDICAL_DIRECTOR:
        denial_reason = f"Role '{identity.role.value}' is restricted from accessing target domain '{domain_filter.value}'."
        db.add_audit_log(AuditLogEntry(
            audit_id=f"aud-{uuid.uuid4().hex[:8]}",
            user_id=identity.user_id,
            user_role=identity.role,
            agent_id="retrieval_engine",
            action="PRE_RETRIEVAL_ROLE_FILTER",
            domain=domain_filter or DomainDomain.CROSS_DOMAIN,
            access_granted=False,
            denial_reason=denial_reason,
            query_summary=query,
            documents_accessed=[],
            guardrail_status="DENIED_ROLE_DOMAINS"
        ))
        return [], denial_reason

    # Query DB with role isolation
    all_permitted_docs = db.get_documents_by_roles([identity.role], domain_filter=domain_filter)

    # Perform keyword matching over permitted documents only
    query_terms = [term.lower() for term in query.split() if len(term) > 2]
    matched_docs = []
    
    for doc in all_permitted_docs:
        doc_text = f"{doc.title} {doc.content} {doc.summary} {' '.join(doc.cpt_codes)} {' '.join(doc.icd10_codes)}".lower()
        if any(term in doc_text for term in query_terms) or not query_terms:
            matched_docs.append(doc)

    db.add_audit_log(AuditLogEntry(
        audit_id=f"aud-{uuid.uuid4().hex[:8]}",
        user_id=identity.user_id,
        user_role=identity.role,
        agent_id="retrieval_engine",
        action="DOCUMENT_RETRIEVAL",
        domain=domain_filter or DomainDomain.CROSS_DOMAIN,
        access_granted=True,
        denial_reason=None,
        query_summary=query,
        documents_accessed=[d.doc_id for d in matched_docs],
        guardrail_status="PASS"
    ))

    return matched_docs, None
