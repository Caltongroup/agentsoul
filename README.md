<div align="center">
  <img src="https://github.com/Caltongroup/agentsoul/blob/main/agentsoul-logo.png?raw=true" alt="AgentSoul Logo" width="280">
  <h1>AgentSoul</h1>
  <p><strong>Local-first • Encrypted • Persistent Memory Backbone for AI Agents</strong></p>
</div>

---

AgentSoul gives your AI agents reliable, encrypted memory that actually persists — without depending on massive context windows or cloud services.

Built because agents kept forgetting.

### Quick Start

```bash
# 1. Install the free core
pip install agentsoul

# 2. Initialize PocketBase (one-time)
python -m agentsoul.setup

# 3. Use in your agent
from agentsoul import AgentSoul

soul = AgentSoul.from_pocketbase(
    url="http://127.0.0.1:8090",
    agent_id="your_agent_001"
)

memory_id = soul.remember("customer", "sarah_chen_001", {
    "name": "Sarah Chen",
    "issue": "Furnace not heating...",
    "priority": "high"
})

memory = soul.recall("customer", "sarah_chen_001")
```

---

### What Makes AgentSoul Different

Most agent memory tools focus on giving agents **knowledge about the user** (emails, calendar, life events).

**AgentSoul focuses on giving agents reliable memory of themselves** — task state, decision history, customer context — with strong encryption and true portability.

---

### Why AgentSoul Is Worth Paying For

The free MIT core gives you the engine.

The **Professional Orchestrator (v0.2)** is the enforcement layer that solves the real problem: **even when agents know they should persist, they usually don't.**

With the Orchestrator:
- ✅ Persistence becomes automatic at natural checkpoints
- ✅ Context is trimmed before it explodes
- ✅ You see measurable wins ("Saved 2,400 tokens this turn")
- ✅ Agents stop forgetting between sessions

This is the difference between "nice-to-have memory" and production-grade reliability.

---

### Open-Core Model

**AgentSoul Core** (MIT License — Free Forever)  
- Full persistence engine (`remember`, `recall`, audit trail)  
- AES-256-GCM encryption with exportable souls  
- SQLite, REST, and PocketBase backends  
- Setup module and clean SDK  

**AgentSoul Orchestrator** (Professional Tier)  
- **Coming in v0.2**  
- Automatic state enforcement at task boundaries  
- Smart context trimming before hitting limits  
- Measurable feedback ("Saved 2,400 tokens this turn")  
- Turns optional memory into production-grade infrastructure  

---

### Pricing

- **Free** — MIT core (unlimited agents)
- **Starter** — $149/yr (up to 10 agents) + basic Orchestrator
- **Professional** — $599/yr (up to 100 agents) — full Orchestrator
- **Enterprise** — Custom (on-prem, SSO, SLA, multi-tenant)

---

### Recommended Usage Pattern

```python
from agentsoul import AgentSoul

# Load persistent soul at the start of every session
soul = AgentSoul.from_pocketbase(
    url="http://127.0.0.1:8090",
    agent_id="your_agent_001"
)

# Work normally...
# ... your agent logic here ...

# Persist at natural breakpoints
soul.remember("task", "current_plan", current_plan_dict)
soul.log_interaction("agent_turn", "completed", {"tokens_used": 1247})

soul.export_soul()   # encrypted portable backup
```

**Key rule:** Never hoard project state in LLM context.  
When approaching limits → persist and trim.

---

### Features (Core)

- ✅ AES-256-GCM encryption with round-trip verification
- ✅ Category + key-based memory lookup
- ✅ Full audit trail
- ✅ System context management
- ✅ Encrypted soul export/import
- ✅ SQLite, REST, and PocketBase backends

---

**Built by Darrell Calton** — from radio/media leadership at Iliad Media Group into practical AI tooling and consulting.

Star the repo if you're tired of agents losing their memory.  
Feedback and early adopters welcome.

[GitHub Issues](https://github.com/Caltongroup/agentsoul/issues) • [License](LICENSE)
