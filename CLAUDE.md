# EX-APPAgent

Autonomous app management agent framework. Hybrid architecture: Claude Code Skill (interaction) + Python engine (data).

## Project Structure

This repo is a Claude Code **marketplace** containing one plugin:

- `.claude-plugin/marketplace.json` — Marketplace manifest
- `plugins/ex-appagent/` — The actual plugin
  - `commands/appagent.md` — Main skill entry point (/appagent)
  - `modules/` — Reusable instruction modules loaded via Read tool
  - `agents/` — Sub-agent instruction files dispatched via Agent tool
  - `templates/` — Templates for initializing new apps
- `docs/superpowers/specs/` — Design specifications
- `docs/superpowers/plans/` — Implementation plans

## Development

This is a Claude Code Plugin packaged as a marketplace. Skills are Markdown instruction files, not traditional code.

- Skill files go in `plugins/ex-appagent/commands/`
- Module files go in `plugins/ex-appagent/modules/`
- Agent files go in `plugins/ex-appagent/agents/`
- Plugin metadata in `plugins/ex-appagent/.claude-plugin/plugin.json`
- Marketplace manifest in `.claude-plugin/marketplace.json`

## Key Design Decisions

- Single entry point: `/appagent` — agent auto-determines what to do
- program.md = static config (human writes), state.json = dynamic data (agent writes)
- File ownership: each file has one writer, atomic writes via temp+rename
- Experience split by category (aso, pricing, growth, product)
- Guardrails: system-enforced (hard) + LLM-enforced (soft)

## Phase Status

- Phase 1 (Skill Foundation): current
- Phase 2 (Python Data Engine): planned
- Phase 3 (Self-Improvement System): planned
