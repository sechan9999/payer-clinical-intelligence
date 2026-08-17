from typing import Dict, Optional
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from app.a2a import generate_agent_card
from app.agent import get_root_agent
from app.approvals import approve_action, dispatch_action
from app.domain import ApprovalStatus
from app.identity import derive_identity
from app.registry import get_agent_registry
from app.store import get_store

app = FastAPI(
    title="Payer Clinical Intelligence System API",
    description="Governed multi-agent back-office fleet on Gemini + ADK over an auditable RAG layer.",
    version="0.1.0"
)


@app.get("/.well-known/agent.json")
@app.get("/a2a/agent-card")
def get_a2a_agent_card():
    return generate_agent_card()


class FleetQueryRequest(BaseModel):
    query: str
    target_domain: Optional[str] = None
    action_type: Optional[str] = None
    params: Optional[dict] = None


@app.get("/")
def read_root():
    return {
        "service": "Payer Clinical Intelligence System",
        "status": "online",
        "version": "0.1.0",
        "governance": "ADK + Server RBAC + SQL Pre-filtering + HITL Approvals",
    }


@app.post("/fleet/query")
def query_fleet(
    request: FleetQueryRequest,
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    agent = get_root_agent()
    raw_token = x_fleet_token or authorization
    result = agent.handle_request(
        query=request.query,
        auth_token=raw_token,
        target_domain=request.target_domain,
        action_type=request.action_type,
        params=request.params,
    )
    return result


@app.get("/fleet/registry")
def get_registry():
    return {"agents": [a.model_dump() for a in get_agent_registry()]}


@app.get("/fleet/approvals")
def list_approvals(
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    raw_token = x_fleet_token or authorization
    identity = derive_identity(raw_token)
    db = get_store()
    
    status_enum = None
    if status:
        try:
            status_enum = ApprovalStatus(status)
        except ValueError:
            pass

    items = db.get_approval_items(status=status_enum)
    return {
        "requested_by_role": identity.role.value,
        "count": len(items),
        "approvals": [i.model_dump() for i in items]
    }


@app.post("/fleet/approvals/{approval_id}/approve")
def approve_human_gate(
    approval_id: str,
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    raw_token = x_fleet_token or authorization
    identity = derive_identity(raw_token)
    ok, message = approve_action(approval_id, identity)
    if not ok:
        raise HTTPException(status_code=403, detail=message)
    return {"success": True, "message": message, "approval_id": approval_id, "approved_by": identity.name}


@app.post("/fleet/approvals/{approval_id}/send")
def dispatch_human_gate(
    approval_id: str,
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    raw_token = x_fleet_token or authorization
    identity = derive_identity(raw_token)
    ok, message, http_status = dispatch_action(approval_id, identity)
    if not ok:
        raise HTTPException(status_code=http_status, detail=message)
    return {"success": True, "message": message, "approval_id": approval_id, "dispatched_by": identity.name}


@app.get("/fleet/audit")
def get_audit_trail(
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    raw_token = x_fleet_token or authorization
    identity = derive_identity(raw_token)
    db = get_store()
    logs = db.get_audit_logs()
    return {
        "viewer_role": identity.role.value,
        "count": len(logs),
        "audit_trail": [l.model_dump() for l in logs]
    }


@app.get("/fleet/events")
def get_activity_stream(
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    raw_token = x_fleet_token or authorization
    identity = derive_identity(raw_token)
    db = get_store()
    activities = db.get_activities()
    return {
        "viewer_role": identity.role.value,
        "count": len(activities),
        "activities": [a.model_dump() for a in activities]
    }
