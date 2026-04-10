# AgentSoul — Framework-Agnostic Agent Persistence Platform

**The memory backbone for production AI agents.**  
Local-first • Portable • Monetizable

[![GitHub stars](https://img.shields.io/github/stars/Caltongroup/agentsoul.svg)](https://github.com/Caltongroup/agentsoul/stargazers)

---

## What is AgentSoul?

AgentSoul is a **standalone, open-core persistence layer** that solves the hardest problem in agent development: **reliable, portable, long-term agent memory**.

Most agents forget after each session. Production agents need memory that:
- Survives reboots and hardware moves (Mac → RPi5 → fleet)
- Works with any framework (Hermes, LangGraph, CrewAI, AutoGen, etc.)
- Never drifts (importance-based consolidation)
- Stays private and zero-cost to run (local-first, no cloud bills)
- Is audit-ready and GDPR-compliant

**Integration takes <10 lines of code.**

---

## Core Features

- **Universal SDK** — Three backends: PocketBase, REST, SQLite
- **True Soul Portability** — Encrypted export/import of complete agent identity + history
- **Importance-Based Decay** — Memories weighted by business signals (recency, frequency, revenue, feedback), not just time
- **Long-Context Consolidation** — Semantic compression prevents drift and hallucination
- **Production Packaging** — One-liner RPi5 deploy + Docker + systemd
- **Framework Agnostic** — Works with any LLM/agent framework

---

## Quick Start

```python
from agentsoul import AgentSoul

# Initialize with your preferred backend
soul = AgentSoul.from_pocketbase(
    url="http://127.0.0.1:8090",
    agent_id="clerk_001"
)

# Remember something
soul.remember("customer", "cust_001", {
    "name": "Alice",
    "payment_style": "reliable",
    "last_interaction": "2026-04-09"
})

# Recall with automatic consolidation
context = soul.recall("customer", "cust_001", consolidate=True)

# Get ready-to-use system prompt
system_prompt = soul.get_system_context("cust_001")

## Commercial Licensing & Support

AgentSoul is **open-core**:

- **MIT License** — Free for open source, personal, and internal use  
- **Startup Tier** — $299/year — Up to 10 agents, email support  
- **Professional Tier** — $999/year — Up to 100 agents, priority support, private Slack channel  
- **Enterprise Tier** — Custom pricing — Unlimited agents, dedicated SLA, on-prem support, custom features

Interested in a commercial license or white-label version?  
Contact: darrell@caltongroup.com or open an issue on GitHub.
