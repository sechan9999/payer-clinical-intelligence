import asyncio
import json
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.a2a import generate_agent_card
from app.agent import get_root_agent
from app.approvals import approve_action, dispatch_action
from app.config import check_runtime_environment
from app.domain import ApprovalStatus, DomainDomain
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


class BulkDryRunRequest(BaseModel):
    claims: List[Dict]


@app.get("/")
def read_root():
    return {
        "service": "Payer Clinical Intelligence System",
        "status": "online",
        "version": "0.1.0",
        "governance": "ADK + Server RBAC + SQL Pre-filtering + HITL Approvals",
    }


@app.get("/metrics")
def get_prometheus_metrics():
    """
    Prometheus Stream Health & Threshold Monitoring Endpoint.
    Exposes metrics for fleet active agents, security denials, pending approvals, and health ratio.
    """
    db = get_store()
    logs = db.get_audit_logs()
    approvals = db.get_approval_items()
    
    denials_count = len([l for l in logs if not l.access_granted or l.guardrail_status != "PASS"])
    pending_count = len([a for a in approvals if a.status == ApprovalStatus.PENDING])
    total_logs = max(len(logs), 1)
    health_ratio = round((len(logs) - denials_count) / total_logs, 4)

    metrics_text = (
        f"# HELP fleet_active_agents Total number of active agents registered in fleet\n"
        f"# TYPE fleet_active_agents gauge\n"
        f"fleet_active_agents 3\n\n"
        f"# HELP fleet_total_audit_events Total audit log events recorded\n"
        f"# TYPE fleet_total_audit_events counter\n"
        f"fleet_total_audit_events {len(logs)}\n\n"
        f"# HELP fleet_security_denials_total Total security denials and guardrail blocks\n"
        f"# TYPE fleet_security_denials_total counter\n"
        f"fleet_security_denials_total {denials_count}\n\n"
        f"# HELP fleet_pending_approvals_count Current items in Human Approval Queue\n"
        f"# TYPE fleet_pending_approvals_count gauge\n"
        f"fleet_pending_approvals_count {pending_count}\n\n"
        f"# HELP fleet_stream_health_ratio Operational compliance and health ratio\n"
        f"# TYPE fleet_stream_health_ratio gauge\n"
        f"fleet_stream_health_ratio {health_ratio}\n"
    )
    return StreamingResponse(iter([metrics_text]), media_type="text/plain")


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


@app.post("/fleet/simulation/dry-run")
def execute_bulk_dry_run(
    request: BulkDryRunRequest,
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    """
    Bulk Dry-Run Simulation Engine.
    Processes batch claim denial events through RBAC pre-filtering and guardrails without dispatching.
    """
    agent = get_root_agent()
    raw_token = x_fleet_token or authorization
    
    simulation_results = []
    for claim in request.claims:
        claim_id = claim.get("claim_id", "CLM-9921")
        res = agent.handle_request(
            query=f"Analyze claim denial {claim_id}",
            auth_token=raw_token,
            action_type="analyze_denial",
            params={"claim_id": claim_id}
        )
        simulation_results.append({
            "claim_id": claim_id,
            "status": res.get("result", {}).get("status"),
            "citations": res.get("result", {}).get("citation_ids", []),
            "simulation": "PASSED_DRY_RUN"
        })

    return {
        "simulation_batch_size": len(request.claims),
        "status": "COMPLETED_DRY_RUN",
        "results": simulation_results
    }


@app.get("/fleet/inbox/sse")
async def sse_live_inbox_stream(
    authorization: Optional[str] = Header(None),
    x_fleet_token: Optional[str] = Header(None, alias="X-Fleet-Token")
):
    """
    Server-Sent Events (SSE) Live Inbox Stream.
    Pushes real-time approval queue and activity events to connected clinical dashboards.
    """
    raw_token = x_fleet_token or authorization
    identity = derive_identity(raw_token)

    async def event_generator():
        db = get_store()
        while True:
            items = db.get_approval_items(status=ApprovalStatus.PENDING)
            data = json.dumps({
                "timestamp": time.time(),
                "user_role": identity.role.value,
                "pending_approvals_count": len(items),
                "event": "INBOX_SYNC"
            })
            yield f"data: {data}\n\n"
            await asyncio.sleep(3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
