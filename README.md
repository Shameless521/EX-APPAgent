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
codex plugin marketplace add Shameless521/EX-APPAgent
```

Or install from a local clone while developing:

```bash
git clone https://github.com/Shameless521/EX-APPAgent.git
codex plugin marketplace add /path/to/EX-APPAgent
```

Then install/enable `ex-appagent` in Codex.

The Python data engine is optional for analysis-only use, but required for automated collection:

```bash
git clone https://github.com/Shameless521/EX-APPAgent.git
cd EX-APPAgent/engine
uv sync
uv run appagent --version
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

Open your app project in Codex after installing the plugin:

```bash
cd /path/to/your-app
codex
```

In Codex, `/appagent` is a skill trigger phrase, not a Claude Code slash command. You can type `/appagent` or describe the request naturally:

```text
/appagent
check revenue trend
what are competitors up to
```

First run automatically guides you through setup (`program.md`, `.appagent/`, API keys, app registration, etc.).

## Existing Claude Code Data

EX-APPAgent stores runtime data in the app project, not in Claude Code. If you used the Claude Code plugin before, keep using the same app project directory:

```text
program.md
.appagent/state.json
.appagent/health.json
.appagent/data/metrics/
.appagent/experiments/
.appagent/insights/
```

Codex will read the same files and continue from the existing state. Only chat-only context from old Claude Code conversations is not migrated unless it was written into `.appagent/`.

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

## Google Play Reports

Google Play revenue, downloads, and ratings are collected from Play Console reports stored in your private Google Cloud Storage report bucket. Add the bucket copied from Play Console > Download reports:

```json
{
  "google_play": {
    "service_account_path": "/path/to/service-account.json",
    "reports_bucket": "pubsite_prod_rev_01234567890987654321"
  }
}
```

Network requests honor `HTTPS_PROXY`, `HTTP_PROXY`, `https_proxy`, and `http_proxy`. The engine retries transient timeout, SSL EOF, 429, and 5xx failures with backoff.

## Requirements

- [Claude Code](https://claude.ai/claude-code) or [Codex CLI](https://github.com/openai/codex)
- Python 3.12+ / [uv](https://docs.astral.sh/uv/)
- Apple Developer account
- Google Play Developer account (optional)
