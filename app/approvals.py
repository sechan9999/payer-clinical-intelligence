from datetime import datetime
import uuid
from typing import List, Optional, Tuple
from app.domain import ActivityEvent, ApprovalItem, ApprovalStatus, DomainDomain, UserIdentity, UserRole
from app.store import DataStore, get_store


def queue_for_human_approval(
    agent_id: str,
    action_type: str,
    target_domain: DomainDomain,
    summary: str,
    payload: dict,
    actor_identity: UserIdentity,
    store: Optional[DataStore] = None,
) -> ApprovalItem:
    """
    Places sensitive actions into the pending Human Approval Queue.
    This path is isolated from direct agent execution.
    """
    db = store or get_store()
    approval_id = f"appr-{uuid.uuid4().hex[:8]}"
    
    item = ApprovalItem(
        approval_id=approval_id,
        agent_id=agent_id,
        action_type=action_type,
        target_domain=target_domain,
        summary=summary,
        payload=payload,
        status=ApprovalStatus.PENDING,
        created_at=datetime.utcnow().isoformat(),
    )
    
    db.add_approval_item(item)
    
    # Emit activity event
    db.record_activity(ActivityEvent(
        event_id=f"evt-{uuid.uuid4().hex[:8]}",
        event_type="APPROVAL_QUEUED",
        domain=target_domain,
        actor_role=actor_identity.role,
        details={
            "approval_id": approval_id,
            "action_type": action_type,
            "summary": summary,
        }
    ))
    
    return item


def approve_action(
    approval_id: str,
    supervisor_identity: UserIdentity,
    store: Optional[DataStore] = None,
) -> Tuple[bool, str]:
    """
    HTTP-only human approval path. Verifies supervisor role (MEDICAL_DIRECTOR or PAYER_ADMIN).
    """
    db = store or get_store()
    
    if supervisor_identity.role not in [UserRole.MEDICAL_DIRECTOR, UserRole.PAYER_ADMIN]:
        return False, f"User role '{supervisor_identity.role.value}' is not authorized to approve items."
        
    items = db.get_approval_items()
    target = next((i for i in items if i.approval_id == approval_id), None)
    if not target:
        return False, f"Approval ID '{approval_id}' not found."

    if target.status != ApprovalStatus.PENDING:
        return False, f"Approval ID '{approval_id}' is in state '{target.status.value}', cannot approve."

    now_iso = datetime.utcnow().isoformat()
    success = db.update_approval_status(approval_id, ApprovalStatus.APPROVED, supervisor_identity.name, now_iso)
    
    if success:
        db.record_activity(ActivityEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            event_type="APPROVAL_GRANTED",
            domain=target.target_domain,
            actor_role=supervisor_identity.role,
            details={"approval_id": approval_id, "approved_by": supervisor_identity.name}
        ))
        return True, "Action successfully approved."
    return False, "Failed to update approval status."


def dispatch_action(
    approval_id: str,
    supervisor_identity: UserIdentity,
    store: Optional[DataStore] = None,
) -> Tuple[bool, str, int]:
    """
    HTTP-only human dispatch path. Can only dispatch items that are APPROVED.
    Returns (success, message, http_status_code).
    Refuses with 409 Conflict if no human signed off prior to dispatch.
    """
    db = store or get_store()
    
    if supervisor_identity.role not in [UserRole.MEDICAL_DIRECTOR, UserRole.PAYER_ADMIN]:
        return False, f"User role '{supervisor_identity.role.value}' is not authorized to dispatch items.", 403

    items = db.get_approval_items()
    target = next((i for i in items if i.approval_id == approval_id), None)
    if not target:
        return False, f"Approval ID '{approval_id}' not found.", 404

    if target.status != ApprovalStatus.APPROVED:
        return False, f"Conflict: Approval ID '{approval_id}' is in '{target.status.value}' state. Human sign-off required prior to dispatch.", 409

    now_iso = datetime.utcnow().isoformat()
    success = db.update_approval_status(approval_id, ApprovalStatus.DISPATCHED, supervisor_identity.name, now_iso)
    
    if success:
        db.record_activity(ActivityEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            event_type="ACTION_DISPATCHED",
            domain=target.target_domain,
            actor_role=supervisor_identity.role,
            details={"approval_id": approval_id, "dispatched_by": supervisor_identity.name}
        ))
        return True, "Action successfully dispatched to external recipient.", 200
    return False, "Failed to update dispatch status.", 500
