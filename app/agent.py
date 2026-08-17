import os
from typing import Dict, Optional
from app.domain import DomainDomain, UserIdentity
from app.fleet import FleetCoordinator
from app.identity import derive_identity
from app.memory import get_memory_bank

# Try loading google.genai if available
try:
    from google import genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


class RootFleetAgent:
    def __init__(self):
        self.coordinator = FleetCoordinator()
        self.memory_bank = get_memory_bank()
        self.use_vertex = os.getenv("GOOGLE_CLOUD_PROJECT") is not None and HAS_GENAI_SDK

    def handle_request(
        self,
        query: str,
        auth_token: Optional[str] = None,
        target_domain: Optional[str] = None,
        action_type: Optional[str] = None,
        params: Optional[dict] = None,
        session_id: Optional[str] = "default_session",
    ) -> Dict:
        """
        Root entry point executing queries through governed fleet.
        Derives identity server-side from bearer token.
        Records history to Session Memory Bank.
        """
        identity = derive_identity(auth_token)
        
        domain_enum = None
        if target_domain:
            try:
                domain_enum = DomainDomain(target_domain)
            except ValueError:
                domain_enum = None

        result = self.coordinator.route_and_execute(
            query=query,
            user_identity=identity,
            target_domain=domain_enum,
            action_type=action_type,
            params=params,
        )

        # Record conversation turn in Memory Bank
        if session_id:
            self.memory_bank.record_turn(
                session_id=session_id,
                role="user",
                content=query,
                metadata={"user_role": identity.role.value}
            )
            self.memory_bank.record_turn(
                session_id=session_id,
                role="assistant",
                content=str(result.get("result", {}).get("response", "")),
                metadata={"coordinator_status": result.get("coordinator_status")}
            )

        return result


# Singleton agent instance
_root_agent_instance: Optional[RootFleetAgent] = None

def get_root_agent() -> RootFleetAgent:
    global _root_agent_instance
    if _root_agent_instance is None:
        _root_agent_instance = RootFleetAgent()
    return _root_agent_instance
