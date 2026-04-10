"""
AgentSoul — Framework-agnostic agent persistence platform.

A standalone, monetizable infrastructure product that solves persistent,
reliable, portable agent memory with AES-256-GCM encryption and
importance-based decay (not time-only).

Quick start:
    from agentsoul import AgentSoul
    
    # PocketBase backend
    soul = AgentSoul.from_pocketbase(
        url="http://127.0.0.1:8090",
        agent_id="my_agent"
    )
    
    # Store memory
    soul.remember("customer", "cust_001", {"name": "Alice", "payment": "reliable"})
    
    # Retrieve memory
    memory = soul.recall("customer", "cust_001")
    
    # Get system prompt
    prompt = soul.get_system_context("cust_001")
"""

from .adapters.sdk import AgentSoul

__version__ = "1.0.0"
__all__ = ["AgentSoul"]
