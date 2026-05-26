# Changelog

All notable changes to AgentSoul will be documented in this file.

## [Unreleased]

### Added
- **Memory Bootstrap Process** (`patterns/memory-bootstrap.md`)
  - Deterministic memory reload on context reset for Hermes integrations
  - Idle detection with lighter resume bootstrap
  - User controls (`memory pause` / `memory resume`)
  - Dynamic token scaling and semantic chunking guardrails
  - Improves reliability without changing AgentSoul core intent

## [0.1.0] - 2026-05-01

### Initial Release
- Core AgentSoul persistence engine
- PocketBase backend support
- Basic remember/recall functionality with encryption