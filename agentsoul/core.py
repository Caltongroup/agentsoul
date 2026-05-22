#!/usr/bin/env python3
"""
AgentSoul Core — Unified interface for memory operations.

Supports three modes:
- "lancedb"   : Semantic vector search only
- "pocketbase": Structured storage only
- "hybrid"    : Both (recommended)
"""

from pathlib import Path
from typing import List, Dict, Optional, Literal

from .memory.lance import recall as lance_recall, recall_formatted as lance_recall_formatted
from .persistence import schema  # for future PocketBase integration


class AgentSoul:
    """
    Unified AgentSoul memory interface.

    Example:
        soul = AgentSoul(backend="hybrid")
        memories = soul.recall("What did Darrell say about retirement?")
    """

    def __init__(
        self,
        backend: Literal["lancedb", "pocketbase", "hybrid"] = "hybrid",
        lancedb_path: Optional[Path] = None,
    ):
        self.backend = backend
        self.lancedb_path = lancedb_path

    def recall(
        self,
        query: str,
        top_k: int = 10,
        min_importance: float = 0.0,
    ) -> List[Dict]:
        """Semantic recall using LanceDB (primary method for context injection)."""
        if self.backend in ("lancedb", "hybrid"):
            return lance_recall(
                query=query,
                top_k=top_k,
                min_importance=min_importance,
                lancedb_path=self.lancedb_path,
            )
        return []

    def recall_formatted(self, query: str, top_k: int = 5) -> str:
        """Return formatted memory block for prompt injection."""
        if self.backend in ("lancedb", "hybrid"):
            return lance_recall_formatted(query, top_k=top_k)
        return "No long-term memory backend configured."

    def remember(self, content: str, role: str = "assistant", **metadata):
        """
        Store a new memory.
        Currently routes to LanceDB ingestion (future: also PocketBase).
        """
        # Placeholder — will connect to ingest.py logic later
        print(f"[AgentSoul] Remember called (backend={self.backend})")
        print(f"  Content: {content[:80]}...")
        return True

    def store_interaction(self, session_id: str, messages: List[Dict], platform: str = "unknown"):
        """Store structured interaction summary (PocketBase path)."""
        # Placeholder for PocketBase integration
        print(f"[AgentSoul] Storing interaction summary for session {session_id}")
        return True


# Convenience factory
def create_agent_soul(backend: str = "hybrid") -> AgentSoul:
    return AgentSoul(backend=backend)