# EX-APPAgent

Autonomous app management agent for Claude Code. Analyzes, optimizes, and grows your apps toward $20/day revenue through data-driven iterative optimization.

Inspired by [autoresearch](https://github.com/karpathy/autoresearch) — the loop never changes, the data evolves.

## What It Does

- Competitor analysis via browser research and third-party platforms
- ASO keyword optimization suggestions
- Conversion funnel analysis
- Feature gap identification
- Revenue and pricing strategy
- Experiment tracking with keep/discard verdicts
- Cross-app experience accumulation

You set goals in `program.md`, the agent does the rest. You only approve plans and handle what AI can't do (App Store submissions, payments, etc.).

## Install

```bash
claude plugins marketplace add Shameless521/EX-APPAgent
claude plugins install ex-appagent
```

## Usage

Navigate to any app project directory and run:

```
/appagent                              # Auto-analyze, agent decides what to focus on
/appagent analyze competitor VSCO       # Specific request in natural language
/appagent how to improve conversion     # Strategy question
/appagent what did we do this week      # Progress report
```

On first run, the agent automatically:
1. Creates a `program.md` template for you to fill in
2. Initializes the `.appagent/` working directory
3. Analyzes your code and competitors
4. Generates initial strategy recommendations

## How It Works

### The Harness Loop

Every `/appagent` run executes the same 10-step cycle:

```
1. Read program.md       → Your goals and constraints
2. Check health          → Is data fresh?
3. Read state            → Where are we?
4. Read metrics          → Latest numbers
5. Read experiments      → Any results?
6. Read experience       → What worked before?
7. Determine priority    → What matters most right now?
8. Execute               → Analyze and generate plans
9. Present summary       → Show you the results
10. Update state         → Record this cycle
```

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

# Guardrails
never_llm:
  - False advertising or fake reviews
  - Copy competitor UI designs

# Current Focus
priorities:
  1. ASO keyword optimization
  2. Improve trial-to-paid conversion
```

The agent reads this file but never modifies it. You change it when strategy shifts.

## Architecture

```
Hybrid: Claude Code Skill + Python Engine (Phase 2)

┌─────────────────────┐     ┌─────────────────────┐
│  /appagent Skill     │     │  Python Engine       │
│  Decision Engine     │◄───►│  Data Collectors     │
│  Code Operations     │files│  Trend Analyzer      │
│  Plan Generation     │     │  Experiment Tracker  │
└─────────────────────┘     └─────────────────────┘
         ▲                           ▲
    You trigger                 cron/launchd
    /appagent                   (Phase 2)
```

**Phase 1 (current):** Skill layer only — competitor analysis via browser, code analysis, strategy generation, plan lifecycle.

**Phase 2 (planned):** Python engine for automated data collection via App Store Connect API.

**Phase 3 (planned):** Self-improvement system with cross-app experience migration and capability expansion.

## Project Structure

```
plugins/ex-appagent/
├── commands/appagent.md            # Main skill entry point
├── modules/                        # Instruction modules
│   ├── harness-loop.md             # Core 10-step cycle
│   ├── cold-start.md               # First-run initialization
│   ├── priority-engine.md          # Priority determination
│   ├── action-lifecycle.md         # Plan approval workflow
│   └── state-manager.md            # State read/write
├── agents/                         # Sub-agent instructions
│   ├── analyst.md                  # Data analysis & strategy
│   ├── competitor-researcher.md    # Market research
│   └── code-operator.md           # Code modifications
└── templates/                      # Initialization templates
    ├── program-template.md         # program.md template
    ├── state-initial.json          # Initial state
    └── health-initial.json         # Initial health
```

## Per-App Data

Each app project gets a `.appagent/` directory (auto-created, gitignored):

```
.appagent/
├── state.json              # Current stage and metrics
├── health.json             # Engine status
├── data/                   # Collected data (Phase 2)
├── experiments/            # Experiment tracking
├── insights/               # Accumulated experience
├── actions/                # Plan lifecycle
│   ├── pending/            # Awaiting your review
│   ├── approved/           # Ready to execute
│   └── rejected/           # With rejection reasons
└── reports/                # Generated reports
```

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- Apple Developer account (for App Store Connect API in Phase 2)

## License

MIT
