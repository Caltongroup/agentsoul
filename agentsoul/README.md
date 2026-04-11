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

### What Makes AgentSoul Different

Most agent memory solutions focus on giving agents **knowledge about the user** (emails, calendar, life events).

**AgentSoul** is built for **agent self-memory** — reliable task state, decision history, customer context, and internal memory that persists across sessions with strong encryption and portability.

- Core is fully open (MIT)
- Orchestrator (v0.2) will be the enforcement layer that makes persistence the *default behavior* instead of an optional afterthought

---

### Open-Core Model

**AgentSoul Core** (MIT License — Free Forever)  
- Full persistence engine (`remember`, `recall`, audit trail)  
- AES-256-GCM encryption with exportable souls  
- SQLite, REST, and PocketBase backends  
- Setup module and clean SDK  

**AgentSoul Orchestrator** (Professional Tier — $999/yr)  
- **Coming in v0.2**  
- Automatically loads state at session start  
- Forces persist + context trimming before hitting limits  
- Delivers measurable feedback ("Saved 2,400 tokens this turn")  
- Turns optional memory into reliable, production-grade infrastructure  

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

# Export encrypted soul for backup
export_soul()
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

---

**Next step:**  
Commit with:
```
git commit -m "README: Final polish with clear differentiation and open-core positioning"
git push
```
