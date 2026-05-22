#!/usr/bin/env python3
"""
AgentSoul LanceDB Memory — Semantic recall over long-term memory.

This module provides vector-based semantic search using LanceDB.
It is designed to work alongside the PocketBase structured backend.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

import httpx
import lancedb

# ─── Configuration ─────────────────────────────────────────────────────────────
DEFAULT_LANCEDB_PATH = Path.home() / "LLM" / "models" / "lancedb" / "agent_memory"
EMBED_URL = "http://localhost:8001/v1/embeddings"
EMBED_MODEL = "nomic-embed-text-v1.5"
DEFAULT_TOP_K = 10

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("agentsoul.lance")


def get_embedding(text: str) -> List[float]:
    """Get embedding vector from local embedding server."""
    text = text[:8000]
    resp = httpx.post(
        EMBED_URL,
        json={"model": EMBED_MODEL, "input": text},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def recall(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    min_importance: float = 0.0,
    lancedb_path: Optional[Path] = None,
) -> List[Dict]:
    """
    Semantic search over stored memories using LanceDB.

    Returns:
        List of memory dicts containing:
        - content, role, source, timestamp, importance, score, session_id
    """
    db_path = lancedb_path or DEFAULT_LANCEDB_PATH
    db = lancedb.connect(str(db_path))

    try:
        table = db.open_table("agent_memory")
    except Exception:
        log.warning("LanceDB table 'agent_memory' not found.")
        return []

    query_embedding = get_embedding(query)

    results = table.search(query_embedding).limit(top_k).to_pandas()

    if min_importance > 0:
        results = results[results["importance"] >= min_importance]

    memories = []
    for _, row in results.iterrows():
        memories.append({
            "content": row.get("content", ""),
            "role": row.get("role", ""),
            "source": row.get("source", ""),
            "timestamp": row.get("timestamp", ""),
            "importance": float(row.get("importance", 0.0)),
            "score": float(row.get("_distance", 0.0)),
            "session_id": row.get("source_session_id", ""),
        })

    return memories


def recall_formatted(query: str, top_k: int = 5) -> str:
    """Return recall results as formatted markdown for prompt injection."""
    results = recall(query, top_k=top_k)
    if not results:
        return "No relevant long-term memories found."

    lines = [f"## Long-term Memory Recall ({len(results)} results)\n"]
    for i, mem in enumerate(results, 1):
        ts = mem["timestamp"][:10] if mem.get("timestamp") else "unknown"
        lines.append(f"**{i}.** [{ts}] ({mem['role']}, {mem['source']})")
        lines.append(f"   {mem['content'][:300]}")
        lines.append("")
    return "\n".join(lines)