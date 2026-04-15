# EX-APPAgent

Autonomous app management agent framework. Hybrid architecture: Claude Code Skill (interaction) + Python engine (data).

## Project Structure

This repo is a Claude Code **marketplace** containing one plugin + Python data engine:

- `.claude-plugin/marketplace.json` — Marketplace manifest
- `plugins/ex-appagent/` — The actual plugin
  - `commands/appagent.md` — Main skill entry point (/appagent)
  - `modules/` — Reusable instruction modules loaded via Read tool
  - `agents/` — Sub-agent instruction files dispatched via Agent tool
  - `templates/` — Templates for initializing new apps
- `engine/` — Python data engine (collectors, analyzers, CLI)
  - `src/appagent_engine/` — Package source
  - `pyproject.toml` — Python 3.12 + uv
- `docs/superpowers/specs/` — Design specifications
- `docs/superpowers/plans/` — Implementation plans

## Development

- Skill files go in `plugins/ex-appagent/commands/`
- Module files go in `plugins/ex-appagent/modules/`
- Agent files go in `plugins/ex-appagent/agents/`
- Engine code in `engine/src/appagent_engine/`
- Extensions in `engine/src/appagent_engine/extensions/`
- Plugin metadata in `plugins/ex-appagent/.claude-plugin/plugin.json`
- Marketplace manifest in `.claude-plugin/marketplace.json`

## Key Design Decisions

- Single entry point: `/appagent` — agent auto-determines what to do
- program.md = static config (human writes), state.json = dynamic data (agent writes)
- File ownership: each file has one writer, atomic writes via temp+rename
- Experience split by category (aso, pricing, growth, product, ops)
- Guardrails: system-enforced (hard) + LLM-enforced (soft)
- Smart collection: no hardcoded schedules, agent reasons about what data to fetch
- Self-learning: ops experience accumulates and improves collection decisions

## Phase Status

- Phase 1 (Skill Foundation): complete
- Phase 2 (Python Data Engine): complete
- Phase 3 (Self-Improvement System): complete
