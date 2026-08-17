import json
import os
from typing import Dict, List, Optional


class SessionMemoryBank:
    """
    Session memory bank supporting Cloud SQL Agent Engine integration
    with offline local memory bank fallback.
    """
    def __init__(self):
        self._memory_store: Dict[str, List[Dict]] = {}

    def record_turn(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        if session_id not in self._memory_store:
            self._memory_store[session_id] = []
        
        self._memory_store[session_id].append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
        })

    def get_history(self, session_id: str) -> List[Dict]:
        return self._memory_store.get(session_id, [])

    def clear_session(self, session_id: str):
        if session_id in self._memory_store:
            del self._memory_store[session_id]


_memory_bank_instance: Optional[SessionMemoryBank] = None

def get_memory_bank() -> SessionMemoryBank:
    global _memory_bank_instance
    if _memory_bank_instance is None:
        _memory_bank_instance = SessionMemoryBank()
    return _memory_bank_instance
