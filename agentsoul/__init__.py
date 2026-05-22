"""
AgentSoul — Persistent memory backbone for AI agents.

Supports hybrid LanceDB (semantic) + PocketBase (structured) storage.
"""

from .core import AgentSoul, create_agent_soul
from .memory.lance import recall, recall_formatted

__version__ = "0.2.0"
__all__ = [
    "AgentSoul",
    "create_agent_soul",
    "recall",
    "recall_formatted",
]