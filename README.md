# EX-APPAgent

Autonomous app operations agent. Set your goals, the agent collects data, analyzes trends, and generates optimization plans — you just approve.

Goal: help every app reach $20/day in revenue.

## Install

**Claude Code:**

```bash
claude plugins marketplace add Shameless521/EX-APPAgent
claude plugins install ex-appagent
```

**Codex CLI:**

```bash
git clone https://github.com/Shameless521/EX-APPAgent.git
```

Then copy `AGENTS.md` to your app project root:

```bash
cp EX-APPAgent/AGENTS.md /path/to/your-app/AGENTS.md
```

## Usage

Navigate to your app project directory:

**Claude Code:**

```bash
/appagent                             # Auto-analyze, agent decides what to do
/appagent check revenue trend         # Specific analysis
/appagent what are competitors up to  # Competitor analysis
/appagent what did we do this week    # Weekly report
```

**Codex CLI:**

Just type naturally — Codex reads `AGENTS.md` automatically:

```
appagent                             # or describe your request directly
check revenue trend
what are competitors up to
```

First run automatically guides you through all setup (API keys, app registration, etc.) — just follow the conversation.

## What It Does

- Auto-collect revenue, downloads, and reviews from App Store Connect / Google Play
- Track ASO keyword ranking changes
- Analyze competitor public data
- Detect data anomalies and diagnose causes
- Manage A/B experiments (hypothesize → observe → keep/discard)
- Gets smarter over time — the agent learns its own data collection strategy
- Budget ROI tracking with ROAS calculation and compliance checks
- Milestone auto-detection — celebrates achievements and unlocks new strategies
- Self-expanding capabilities — agent proposes new analysis tools when needed

## What You Do

1. Fill in `program.md` (goals, competitors, budget, etc.)
2. Run `/appagent` regularly
3. Approve plans the agent generates
4. Handle what AI can't do (App Store submissions, payments, etc.)

## Update

Skill layer updates automatically with the plugin. Data engine version is checked on each `/appagent` run — you'll be prompted to upgrade when available.

## Requirements

- [Claude Code](https://claude.ai/claude-code) or [Codex CLI](https://github.com/openai/codex)
- Python 3.12+ / [uv](https://docs.astral.sh/uv/)
- Apple Developer account
- Google Play Developer account (optional)
