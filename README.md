# EX-APPAgent

Autonomous app management agent for Claude Code. Analyzes, optimizes, and grows your apps toward $20/day revenue through data-driven iterative optimization.

Inspired by [autoresearch](https://github.com/karpathy/autoresearch) — the loop never changes, the data evolves.

## What It Does

- Automated data collection from App Store Connect & Google Play APIs
- ASO keyword ranking tracking and optimization
- Competitor analysis via public data
- Trend analysis with anomaly detection
- Experiment tracking with keep/discard verdicts
- Self-learning collection strategy (gets smarter over time)
- Cross-app experience accumulation

You set goals in `program.md`, the agent does the rest. You only approve plans and handle what AI can't do (App Store submissions, payments, etc.).

## Install

```bash
claude plugins marketplace add Shameless521/EX-APPAgent
claude plugins install ex-appagent
```

That's it. On first run, `/appagent` will guide you through everything else — engine installation, API key configuration, app registration — all within the conversation.

## Usage

Navigate to any app project directory and run:

```
/appagent                              # Auto-analyze, agent decides what to focus on
/appagent analyze competitor VSCO       # Specific request in natural language
/appagent how to improve conversion     # Strategy question
/appagent what did we do this week      # Progress report
```

On first run, the agent automatically:
1. Installs the Python data engine (if not present)
2. Guides you through API key setup (App Store Connect, Google Play)
3. Auto-detects your app's bundle IDs from project files (Flutter, iOS, Android)
4. Creates a `program.md` template for you to fill in
5. Runs first data collection
6. Analyzes your code and competitors
7. Generates initial strategy recommendations

## Update

**Skill layer (Markdown instructions):** Updates automatically when the plugin syncs with git. No action needed.

**Python data engine:** The agent auto-detects when a new version is available each time you run `/appagent`. If an update exists, it will ask:

```
Data engine update available (0.1.0 → 0.2.0). Update now?
```

Agree, and it upgrades in one command. Decline, and it continues with the current version — old versions remain compatible.

**Manual update** (if needed):

```bash
uv tool install --upgrade "appagent-engine @ git+https://github.com/Shameless521/EX-APPAgent#subdirectory=engine"
```

## How It Works

### The Harness Loop

Every `/appagent` run executes the same cycle:

```
1.   Read program.md       → Your goals and constraints
2.   Check health & engine → Is engine installed and up to date?
3.   Read state            → Where are we?
3.5  Smart collection      → Agent decides what data to refresh (context-aware)
4.   Read metrics          → Latest numbers
5.   Read experiments      → Any results?
6.   Read experience       → What worked before?
7.   Determine priority    → What matters most right now?
8.   Execute               → Analyze and generate plans
9.   Present summary       → Show you the results
9.5  Reflect               → Learn from this cycle's data decisions
10.  Update state          → Record this cycle
```

### Smart Collection (Step 3.5)

No hardcoded schedules. The agent reasons about what data to collect each run:

- **User intent**: "看看收入" → only refresh metrics
- **Active experiments**: ASO experiment → prioritize keyword rankings
- **Data gaps**: Missing 3 days of metrics → auto-backfill
- **Past experience**: "Last time I skipped reviews during a pricing experiment, I missed user complaints" → collect reviews this time
- **Freshness**: Data from 1 hour ago → skip, data from 3 days ago → refresh

The collection strategy **learns over time** through the ops experience system (Step 9.5).

### Self-Learning (Step 9.5)

After each analysis, the agent reflects:

- "Did I collect the right data? Was something missing?"
- "Did I waste API calls on data I didn't use?"
- "What patterns do I see in this app's data behavior?"

Lessons are recorded in `experience-ops.json` and inform future collection decisions. Week 1 the agent collects by instinct; by week 4 it has learned your app's patterns.

### Priority System

The agent automatically determines what's most important:

| Priority | Trigger | Action |
|----------|---------|--------|
| 1 | Milestone reached | Celebrate, unlock new strategies |
| 2 | Plans awaiting review | Present for approval |
| 3 | Experiment complete | Judge keep/discard |
| 4 | Data anomaly | Diagnose and respond |
| 5 | Normal | Push current focus forward |

### program.md

Your only job is defining the strategy in `program.md`:

```markdown
# Identity
name: MyApp
positioning: AI photo editor for enthusiasts

# Target
north_star: Daily pure revenue $20
milestones:
  - $1/day → validated (unlock: ad spend)
  - $5/day → growing (unlock: higher budget)
  - $20/day → target achieved

# Competitors
watch_list:
  - VSCO (priority) — focus: pricing, new features
  - Snapseed — focus: free model monetization

# Current Focus
priorities:
  1. ASO keyword optimization
  2. Improve trial-to-paid conversion
```

The agent reads this file but never modifies it. You change it when strategy shifts.

## Architecture

```
Hybrid: Claude Code Skill + Python Data Engine

┌──────────────────────────┐     ┌──────────────────────────┐
│  /appagent Skill          │     │  Python Data Engine       │
│  Decision & Reasoning     │     │  collectors/              │
│  Smart Collection Logic   │◄───►│    appstore, googleplay,  │
│  Analysis & Plans         │files│    aso, competitors        │
│  Self-Learning Reflection │     │  analyzer/                │
│  Code Operations          │     │    trends, experiments     │
└──────────────────────────┘     └──────────────────────────┘
         ▲                                ▲
    You trigger                      On-demand via
    /appagent                     appagent collect
```

**Skill layer** runs inside Claude Code (uses your subscription, no API key). Handles all LLM-powered reasoning, decision-making, and code generation.

**Python engine** handles data collection, storage, and number crunching. No LLM calls. Installed as a CLI tool (`appagent`).

## Data Engine CLI

```bash
appagent collect                                   # Collect all data for all apps
appagent collect --app MyApp                       # Single app
appagent collect --only metrics,aso                # Selective categories
appagent collect --only metrics --dates backfill   # Auto-fill missing dates
appagent collect --dry-run                         # Preview without executing
appagent health                                    # Show engine status & data freshness
appagent --version                                 # Show installed version
```

## Project Structure

```
EX-APPAgent/
├── plugins/ex-appagent/
│   ├── commands/appagent.md        # Main skill entry point
│   ├── modules/                    # Instruction modules
│   │   ├── harness-loop.md         # Core cycle with smart collection
│   │   ├── cold-start.md           # Zero-config onboarding
│   │   ├── priority-engine.md      # Priority determination
│   │   ├── action-lifecycle.md     # Plan approval workflow
│   │   └── state-manager.md        # State read/write
│   ├── agents/                     # Sub-agent instructions
│   │   ├── analyst.md              # Data analysis & strategy
│   │   ├── competitor-researcher.md# Market research
│   │   └── code-operator.md        # Code modifications
│   └── templates/                  # Initialization templates
├── engine/                         # Python data engine
│   ├── pyproject.toml              # Python 3.12 + uv
│   └── src/appagent_engine/
│       ├── cli.py                  # CLI entry point
│       ├── config.py               # Config & app registry
│       ├── health.py               # Health reporting
│       ├── guardrails.py           # System-enforced safety
│       ├── scheduler.py            # macOS launchd (optional)
│       ├── collectors/             # Data collectors
│       │   ├── appstore.py         # App Store Connect API
│       │   ├── googleplay.py       # Google Play Developer API
│       │   ├── aso.py              # Keyword ranking tracker
│       │   ├── competitor.py       # Public data collector
│       │   ├── reviews.py          # Unified review collector
│       │   └── assembler.py        # Daily metrics assembler
│       ├── analyzer/               # Data analysis
│       │   ├── trends.py           # WoW/MoM/anomaly detection
│       │   └── experiment.py       # Experiment pre-calculator
│       └── store/                  # Data storage
│           ├── writer.py           # Atomic file writer
│           └── experience.py       # Experience library manager
└── docs/superpowers/               # Design specs & plans
```

## Per-App Data

Each app project gets a `.appagent/` directory (auto-created, gitignored):

```
.appagent/
├── state.json              # Current stage and metrics
├── health.json             # Engine status & data freshness
├── data/
│   ├── metrics/            # Daily metrics (YYYY-MM-DD.json)
│   ├── competitors/        # Competitor profiles
│   └── aso/                # Keyword rankings
├── experiments/            # Experiment tracking
│   ├── active.json         # Running experiments
│   ├── log.jsonl           # All experiment records
│   └── pre-calc/           # Engine pre-calculations
├── insights/               # Accumulated experience
│   ├── experience-aso.json
│   ├── experience-pricing.json
│   ├── experience-growth.json
│   ├── experience-product.json
│   └── experience-ops.json # Self-learning collection patterns
├── actions/                # Plan lifecycle
│   ├── pending/            # Awaiting your review
│   ├── approved/           # Ready to execute
│   └── rejected/           # With rejection reasons
└── reports/                # Generated reports
```

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) (for the data engine)
- Apple Developer account (for App Store Connect API)
- Google Play Developer account (optional, for Android data)

## Development Phases

- **Phase 1 (complete):** Skill foundation — harness loop, cold start, competitor analysis, plan lifecycle
- **Phase 2 (complete):** Python data engine — automated collection, trend analysis, experiment pre-calc
- **Phase 3 (planned):** Self-improvement system — cross-app experience migration, capability expansion

## License

MIT
