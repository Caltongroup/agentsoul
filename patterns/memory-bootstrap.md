# AgentSoul Memory Bootstrap Process

**Status:** Production Pattern  
**Applies to:** Hermes + AgentSoul integrations  
**Goal:** Survive context resets reliably without changing AgentSoul's core intent.

## Core Principle
AgentSoul is the memory process. It must survive context resets in a deterministic, auditable, and user-controllable way. Storage layers are replaceable.

## When to Use This Pattern
Use this when running AgentSoul with Hermes (or any system that resets context regularly). This pattern ensures critical memory is automatically reloaded on startup and after long idle periods.

## Bootstrap Process (Startup)
1. Detect new session or long idle gap
2. Execute the AgentSoul bootstrap rule set:
   - Retrieve highest-importance, stable memories for the current entity
   - Apply stability filter (facts expected to remain valid 7+ days)
   - Token budget: Default 1400 tokens (configurable via `AGENTSoul_BOOTSTRAP_TOKEN_BUDGET`)
   - Smart limit: Never exceed 35% of remaining context window, with dynamic scaling based on query complexity
3. Log the bootstrap event

## Idle Handling
- After 4 hours of inactivity → mark session as idle
- On next message → run lighter "resume" bootstrap
- Never assume the user is finished for the day

## User Controls
- `memory pause`
- `memory resume`

## Guardrails
- Dynamic token scaling
- Telegram: 1800–1900 character target, 2100 hard cap
- Semantic chunking when approaching limits
- Error handling with graceful fallback
- Full audit logging

## Value
This pattern makes AgentSoul more reliable in real-world, long-running agent environments without altering its fundamental design.