# AgentSoul — Framework-Agnostic Agent Persistence Platform

**The memory backbone for production AI agents. Works with any LLM framework.**

---

## What is AgentSoul?

AgentSoul is a **standalone, monetizable infrastructure product** that solves the hardest problem in agent development: **persistent, reliable, portable agent memory**.

Unlike chatbots that forget after each session, AI agents in production need:
- **Long-term memory** of customers, interactions, and patterns
- **Memory portability** (dev Mac → customer RPi5 → fleet of devices)
- **Zero drift** (consolidation + decay prevents hallucination)
- **Framework flexibility** (works with Hermes, LangGraph, CrewAI, AutoGen, etc.)
- **Compliance-ready** (audit trails, GDPR delete, encryption)

AgentSoul provides all of this in **<10 lines of Python code**.

---

## Core Features

### 1. **Universal Memory Interface** (SDK)
One Python class, three backends: SQLite (standalone), REST (cloud), PocketBase (local server).

```python
from agentsoul import AgentSoul

# Initialize once, works everywhere
soul = AgentSoul.from_rest(
    url="http://localhost:5001",
    agent_id="clerk_001",
    token="your_api_token"
)

# Store memory
soul.remember("customer", "cust_001", {
    "name": "Alice",
    "payment_style": "reliable",
    "contact": "sms"
})

# Retrieve with automatic consolidation
context = soul.recall("customer", "cust_001", consolidate=True)

# Inject into agent
system_prompt = soul.get_system_context("cust_001")
```

### 2. **Importance-Based Decay** (Not just time)
Memories decay based on **business signals**, not just age:
- Recent interactions get higher weight
- Frequently-mentioned facts persist longer
- High-value customers = higher memory weight
- Explicit feedback signals boost importance

Result: Agents stay focused on what matters.

### 3. **Soul Portability** (Export/Import)
Move a complete agent soul with one command:

```python
# On Mac (dev)
artifact = soul.export_soul(passphrase="secure_123")
# Save artifact for transfer to RPi5

# On RPi5 (production)
soul_prod.import_soul(artifact, "secure_123")
# Complete state instantly available
```

### 4. **System Prompt Injection**
Pre-loaded context before every agent interaction:

```
You are serving customer_001.

CONSOLIDATED MEMORY:
- Reliability: highly reliable (95%)
- Prefers: SMS, morning
- Service types: HVAC repair, filter replacement
- Notes: Always pays on time

Respond naturally and helpfully.
```

### 5. **Production-Ready Packaging**
- **REST API** with Bearer token auth
- **Docker** support for cloud/Kubernetes
- **RPi5 one-liner** deployment
- **PocketBase** integration (local SQLite server)
- **Audit trails** for compliance

---

## Comparison: AgentSoul vs Alternatives

| Feature | AgentSoul | Mem0 | Zep | Letta |
|---------|-----------|------|-----|-------|
| **Framework Agnostic** | ✓ Any LLM | ✓ | ✓ | ✗ (Letta-specific) |
| **Soul Portability** | ✓ Export/import | ✗ | ✗ | ✗ |
| **Local-First** | ✓ SQLite + REST | ✗ (SaaS) | ✗ (SaaS) | ✓ |
| **Importance Decay** | ✓ Business-signals | ✗ (Time-only) | ✗ (Time-only) | ? |
| **Encryption** | ✓ AES-256-GCM | ✗ | ✗ | ? |
| **GDPR Ready** | ✓ Delete + audit | ✗ | ✗ | ? |
| **Standalone License** | ✓ MIT/Commercial | ✗ (SaaS) | ✗ (SaaS) | ✓ |
| **Python SDK** | ✓ <10 lines | ? | ✗ | ✓ |
| **RPi5 Deploy** | ✓ One-liner | ✗ | ✗ | ✗ |
| **Cost** | **$0-999/yr** | $9-99/mo | $0-299/mo | Free |

**AgentSoul wins on: Portability + Local-first + Framework flexibility**

---

## Quick Start

### 1. Install AgentSoul

```bash
git clone https://github.com/agentsoul/agentsoul
cd agentsoul
pip install -e .
```

### 2. Initialize Database

```bash
python -m agentsoul.persistence.schema
# Creates SQLite tables
```

### 3. Start REST API (optional)

```bash
python -m agentsoul.adapters.rest_api
# Listening on http://127.0.0.1:5001
```

### 4. Use in Your Agent

```python
from agentsoul import AgentSoul

soul = AgentSoul.from_sqlite(
    db_path="/path/to/db.db",
    agent_id="my_agent"
)

# Store memory
soul.remember("entity", "user_123", {"age": 30, "role": "buyer"})

# Recall with consolidation
memory = soul.recall("entity", "user_123")

# Get system prompt
prompt = soul.get_system_context("user_123")
```

---

## Licensing & Pricing

### Open Source (MIT)
- **Free for development and educational use**
- Local SQLite backend only
- Full source code

### Commercial (Annual)

| Tier | Price | Agents | Support |
|------|-------|--------|---------|
| Startup | $299/yr | 10 | Email |
| Professional | $999/yr | 100 | Priority |
| Enterprise | Custom | ∞ | Dedicated SLA |

**Use the open-source version for free. Pay only if you deploy commercially.**

---

## Use Cases

### 1. Mobile Service Techs (HVAC, Plumbing, Electrical)
Portable clerk agent on RPi5, carried to every job site.

### 2. Virtual Assistant Services
Agents that remember customer preferences across devices.

### 3. Conversational AI (SaaS)
Long-term memory for chatbots that scale.

### 4. Enterprise Agent Fleet
Multiple agents sharing memory via central PocketBase.

### 5. AI Research
Persistent memory for agent experiments without drift.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│           Agent Framework                   │
│    (Hermes, LangGraph, CrewAI, AutoGen)    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   AgentSoul SDK      │
        │  (Python interface)  │
        └──────────────┬───────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌─────────┐  ┌──────────┐  ┌────────┐
    │ SQLite  │  │ REST API │  │ MCP    │
    │ Local   │  │ (HTTP)   │  │Server  │
    └────┬────┘  └────┬─────┘  └────┬───┘
         │            │             │
         └────────────┼─────────────┘
                      ▼
         ┌────────────────────────────┐
         │  PocketBase Data Store     │
         │  (agent_soul_memories,     │
         │   interactions, audit)     │
         └────────────────────────────┘
```

---

## Security & Compliance

- **Encryption**: AES-256-GCM (NIST-grade)
- **Key Derivation**: PBKDF2-HMAC-SHA256 (480k iterations)
- **Audit Trails**: All actions logged
- **GDPR**: DELETE endpoint for memory removal
- **Authentication**: Bearer tokens (pluggable)

---

## Roadmap

- [ ] Vector search (semantic similarity)
- [ ] Multi-agent collaboration
- [ ] Graph memory (relationship mapping)
- [ ] LLM-powered summarization
- [ ] Web UI dashboard
- [ ] Kubernetes operator
- [ ] OpenAI Assistant integration

---

## Contributing

Contributions welcome! Submit PRs to [GitHub](https://github.com/agentsoul/agentsoul).

---

## Support

- **Docs**: https://agentsoul.docs
- **GitHub Issues**: https://github.com/agentsoul/agentsoul/issues
- **Email**: support@agentsoul.io
- **Discord**: [Join community](https://discord.gg/agentsoul)

---

**AgentSoul: The memory backbone your agents deserve.**
