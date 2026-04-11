<div align="center">
  <img src="https://github.com/Caltongroup/agentsoul/blob/main/agentsoul-logo.png?raw=true" alt="AgentSoul Logo" width="280">
  <h1>AgentSoul</h1>
  <p><strong>Local-first • Encrypted • Persistent Memory Backbone for AI Agents</strong></p>
</div>

---

**AgentSoul** gives your AI agents reliable, encrypted memory that actually persists — without depending on massive context windows or cloud services.

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

### Open-Core Model

**AgentSoul Core** (MIT License — Free Forever)  
- Full persistence engine (`remember`, `recall`, audit trail)  
- AES-256-GCM encryption  
- SQLite, REST, and PocketBase backends  
- Setup module and clean SDK  

**AgentSoul Orchestrator** (Professional Tier — $999/yr)  
- **Coming in v0.2**  
- The enforcement layer that makes persistence the *default behavior*  
- Automatically loads state at session start  
- Forces persist + context trimming before hitting limits  
- Delivers measurable feedback ("Saved 2,400 tokens this turn")  

This split keeps the foundation open for easy adoption while protecting the key piece that forces agents to actually use persistent memory instead of hoarding context.

---

### Recommended Usage Pattern

```python
from agentsoul import AgentSoul

# Load persistent soul at the start of every session
soul = AgentSoul.from_pocketbase(url="http://127.0.0.1:8090", agent_id="your_agent_001")

# Work normally...
# ... your agent logic here ...

# Persist at natural breakpoints
soul.remember("task", "current_plan", current_plan_dict)
soul.log_interaction("agent_turn", "completed", {"tokens_used": 1247})

# Export encrypted soul for backup/portability
soul.export_soul()
```

**Key rule:** Never hoard project state in LLM context.  
When approaching context limits → persist and trim.

---

### Features (Core)

- ✅ AES-256-GCM encryption with round-trip verification
- ✅ Category + key-based memory lookup
- ✅ Full audit trail
- ✅ System context management
- ✅ Encrypted soul export/import
- ✅ Three backends (SQLite recommended for local-first)

### Monetization

- **MIT** — Free open core
- **Startup** — $299/yr (10 agents)
- **Professional** — $999/yr (100 agents) — includes Orchestrator (v0.2)
- **Enterprise** — Custom

---

**Built by Darrell Calton** — blending media leadership at Iliad Media Group with hands-on AI tooling.

Star the repo if you're tired of agents losing their memory.  
Feedback and early adopters welcome.

[GitHub Issues](https://github.com/Caltongroup/agentsoul/issues) • [License](LICENSE)
