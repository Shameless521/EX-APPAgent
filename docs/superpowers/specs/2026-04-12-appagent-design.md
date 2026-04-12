# EX-APPAgent Design Spec

## Overview

EX-APPAgent is an autonomous app management agent framework that can take over the full operational lifecycle of any app — feature iteration, marketing, market research, competitor analysis, and revenue optimization. The user sets goals and constraints via `program.md`, the agent autonomously analyzes data, generates action plans, and the user approves and executes what AI cannot do alone.

Core philosophy derived from [autoresearch](https://github.com/karpathy/autoresearch):
- **program.md** — human defines direction, does not write code
- **Harness loop** — fixed cycle that never changes, but content evolves with each iteration
- **Self-improvement** — strategy evolution through experiment keep/discard + capability expansion

Target: $20/day pure revenue per app, achieved through data-driven iterative optimization.

## Architecture

### Hybrid Architecture (Approach C)

Two-layer system running entirely on the user's local Mac:

```
Local Mac
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Claude Code + /appagent Skill         Python Engine       │
│  ┌──────────────────────┐       ┌──────────────────────┐   │
│  │ Decision Engine      │       │ Data Collectors      │   │
│  │ Code Operations      │◄─────►│ Trend Analyzer       │   │
│  │ Action Plan Output   │ files │ Experiment Tracker   │   │
│  │ Human Task Queue     │       │ Experience Database   │   │
│  └──────────────────────┘       └──────────────────────┘   │
│         ▲                              ▲                   │
│         │                              │                   │
│    User triggers                  cron/launchd             │
│    /appagent                      scheduled tasks          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Skill Layer (Green):**
- Runs inside Claude Code, uses existing subscription (no API key needed)
- Reads project code, generates action plans, writes code changes
- Reads analysis data from Python engine via `.appagent/` directory
- Handles all LLM-powered reasoning, decision-making, and code generation

**Python Engine (Blue):**
- Pure Python, no LLM calls required
- Handles data collection, storage, trend analysis, experiment tracking
- Runs via cron/launchd for scheduled collection (2-3 times daily)
- Communicates with Skill layer through `.appagent/` file directory

**Data Exchange:**
Both layers communicate through the `.appagent/` directory within each app project. Python engine writes data, Skill layer reads it. No network protocol, no database server — just files.

## program.md — The Core Directive

Each app project contains a `program.md` at the root. This is the only file the human writes. The agent reads it but never modifies it. Changing this file is how the human "programs" the agent's behavior.

### Structure

```markdown
# Identity
name: AppName
platform: iOS + Android (Flutter)
tech_stack: Flutter 3.x / Dart / Firebase
positioning: One-line description of what the app is and who it's for
differentiator: What makes this app different from competitors
app_store_id: com.example.appname
store_url: https://apps.apple.com/app/id123456

# Target
north_star: Daily pure revenue $20
milestones:
  - $1/day → monetization model validated (unlock: small ad spend)
  - $5/day → stable growth phase (unlock: increase daily budget to $10)
  - $20/day → target achieved (unlock: consider new feature lines)
current_daily_revenue: $X
current_daily_downloads: ~N

# Users
primary: Target demographic and behavior description
pain_points:
  - Pain point 1
  - Pain point 2
willingness_to_pay: Low / Medium / High
discovery_channels: Where users find this type of app

# Monetization
model: freemium + subscription / paid / ad-supported
pricing:
  - Free tier: what's included
  - Paid tier: price and what's included
  - One-time purchases: items and prices
current_conversion:
  - download→register: X%
  - register→trial: X%
  - trial→paid: X%

# Budget
daily_limit: $5-10 (adjusts by milestone stage)
min_roas: 1.5 (minimum $1.5 revenue per $1 spent)
preferred_channels:
  - Priority: ASO optimization, social media content (free)
  - Secondary: Apple Search Ads (paid, requires data support)
  - Not now: channels not worth the budget yet

# Competitors
watch_list:
  - CompetitorA (priority) — focus: pricing strategy, new features, ASO keywords
  - CompetitorB — focus: free model monetization, feature scope
analysis_dimensions:
  - Feature comparison / pricing / ASO keywords / review sentiment / update frequency

# Guardrails
never:
  - False advertising or fake reviews
  - Copy competitor UI designs
  - Collect or upload user data without authorization
  - Exceed daily_limit in a single day
  - Modify multiple monetization parameters simultaneously
caution:
  - Price reductions require at least 7 days of data support
  - Removing existing features requires confirming no active users
  - New permissions (beyond core functionality) require human approval

# Experiments
rules:
  - Single variable per experiment
  - Minimum observation period: 7 days
  - Significance threshold: >5% change in core metric
  - 2 consecutive failures on same approach → pivot direction
log: .appagent/experiments/log.jsonl

# Current Focus
stage: From $X → $Y/day
priorities:
  1. Priority task 1
  2. Priority task 2
  3. Priority task 3
```

### Design Principles

- **Milestone-driven**: Not a single leap to $20/day. Each milestone unlocks new strategy space (higher budgets, more aggressive experiments).
- **Guardrails are tiered**: `never` = absolute prohibition, `caution` = requires data support or human approval.
- **Scientific experiments**: Single-variable principle + minimum observation period + clear significance threshold. Prevents the agent from making random changes with no way to attribute results.
- **Aligned with autoresearch**: program.md is the human's only file. The agent reads it, never writes it. Modifying this file is "programming" the agent.

## Project Directory Structure

### Per-App Structure

```
MyApp/
├── program.md                      # Human-written agent directive
├── .appagent/
│   ├── state.json                  # Current state (stage, latest metrics snapshot)
│   ├── data/
│   │   ├── metrics/
│   │   │   └── 2026-04-12.json     # Daily: downloads, revenue, ratings, rankings
│   │   ├── competitors/
│   │   │   └── vsco.json           # Competitor profile: features, pricing, reviews
│   │   └── aso/
│   │       └── keywords.json       # Keyword rankings and search volume
│   ├── experiments/
│   │   ├── log.jsonl               # All experiment records (append-only)
│   │   └── active.json             # Currently running experiments
│   ├── insights/
│   │   └── experience.json         # This app's accumulated experience
│   ├── actions/
│   │   ├── pending.md              # Plans awaiting user approval
│   │   ├── approved/               # Approved, ready to execute
│   │   └── history/                # Archived past plans
│   └── reports/
│       └── weekly-summary.md       # Weekly summary report
├── src/                            # App source code (existing)
└── ...
```

### Global Structure

```
~/.appagent/
├── global-insights/
│   └── experience.json             # Cross-app universal experience
├── config.json                     # Global settings (API keys, defaults)
└── apps.json                       # Registry of all managed apps
```

**Experience flow**: When the agent writes an insight to the per-app `insights/`, it evaluates whether the insight has cross-app applicability. If yes, it also syncs to `~/.appagent/global-insights/`. When analyzing any app, the agent reads both local and global experience.

## Command System

### Single Entry Point

```
/appagent                           # Agent auto-determines what to do
/appagent <natural language>        # Specific request in plain language
```

No subcommands to memorize. The agent reads current state and decides priority automatically.

### Smart Main Loop (Harness)

When `/appagent` is triggered without arguments:

```
1. Read program.md              → Understand goals and constraints
2. Read state.json              → Current stage and last analysis
3. Read data/metrics/           → Latest data from Python engine
4. Read experiments/            → In-progress experiment results
5. Read insights/               → Historical experience (local + global)
6. Auto-determine priority      → What's most important right now?
7. Analyze + decide             → Generate action plan
8. Write actions/pending.md     → Await user approval
9. Update state.json            → Record this analysis cycle
```

The loop never changes. The data changes. This is the harness.

### Priority Determination

The agent automatically selects the highest-priority action:

| Priority | Condition | Action |
|----------|-----------|--------|
| 1. Urgent | Pending actions awaiting approval | Present for review |
| 2. Experiment | An experiment's observation period ended | Judge keep/discard, write insight |
| 3. Anomaly | Metrics show abnormal change (>20% drop) | Diagnose cause, generate response plan |
| 4. Milestone | A milestone has been reached | Update stage, unlock new strategies |
| 5. Routine | Normal state | Push forward Current Focus priorities |

### Natural Language Examples

```
/appagent                                    → Auto-analyze, auto-prioritize
/appagent look at what VSCO has been up to   → Competitor analysis
/appagent how to get downloads from 30 to 100 → Growth strategy
/appagent what did we do this week            → Weekly report
/appagent did the keyword change work         → Experiment status check
/appagent analyze recent negative reviews     → Review analysis
```

## Python Engine

### Module Structure

```
engine/
├── collectors/                  # Data collectors
│   ├── appstore.py              # App Store Connect API (revenue/downloads/ratings)
│   ├── reviews.py               # User review fetching and parsing
│   ├── aso.py                   # Keyword ranking tracking
│   └── competitor.py            # Competitor public data scraping
├── analyzer/
│   ├── trends.py                # Trend calculation (WoW, MoM, anomaly detection)
│   └── experiment.py            # Experiment verdict engine (keep/discard)
├── store/
│   ├── writer.py                # Write to .appagent/data/
│   └── experience.py            # Experience library management (local + global)
├── scheduler.py                 # Local cron/launchd wrapper
└── cli.py                       # CLI entry point
```

### CLI Commands

```bash
appagent collect                 # Manual one-time data collection
appagent collect --app PhotoCraft # Collect for specific app
appagent daemon                  # Start scheduled collection (via launchd)
appagent daemon stop             # Stop scheduled collection
```

### Data Collection

- **App Store Connect API**: Revenue, downloads, subscriptions, ratings — via API Key (free with Apple Developer account)
- **Google Play Developer API**: Same data for Android apps
- **User Reviews**: Fetched via store APIs, parsed for keywords and sentiment
- **ASO Keywords**: Track ranking changes for target keywords
- **Competitor Data**: Public store page scraping (features, pricing, ratings, review highlights)

Collection frequency: 2-3 times daily via launchd, sufficient for App Store's daily data granularity.

### Data Format

**Daily metrics** (`data/metrics/2026-04-12.json`):
```json
{
  "date": "2026-04-12",
  "revenue": 2.3,
  "downloads": 45,
  "rating": 4.6,
  "ratings_count": 234,
  "reviews_new": 3,
  "active_subscriptions": 18,
  "keyword_rankings": {
    "photo editor": 12,
    "film camera": 18
  }
}
```

**Experiment record** (`experiments/log.jsonl`):
```json
{
  "id": "exp_001",
  "app": "PhotoCraft",
  "date_start": "2026-04-05",
  "date_end": "2026-04-12",
  "action": "aso_keyword_add_film_camera",
  "hypothesis": "Adding keyword 'film camera' will improve search visibility",
  "variable": "aso_keywords",
  "metric_before": {"daily_downloads": 30, "keyword_rank": null},
  "metric_after": {"daily_downloads": 42, "keyword_rank": 18},
  "delta_pct": 40,
  "verdict": "keep",
  "insight": "film camera is an effective keyword — high search volume, medium competition",
  "cross_app_applicable": true
}
```

## Self-Improvement System

### Strategy Evolution (Experience Accumulation)

Every experiment follows the autoresearch cycle:
1. Agent proposes a change (hypothesis)
2. Change is implemented (after user approval)
3. Python engine tracks metrics for the observation period
4. At period end, `analyzer/experiment.py` auto-judges: **keep** (metric improved >5%) or **discard** (no improvement or regression)
5. Insight extracted and written to experience library
6. If cross-app applicable, synced to global experience

Over time, the agent builds a growing knowledge base of what works and what doesn't, across all apps. When analyzing a new app, it draws on this accumulated wisdom.

### Capability Expansion (Learning New Skills)

When the agent identifies a capability gap:
1. Agent generates a "capability expansion request" in `actions/pending.md`
2. Request includes: what's needed, why, and a proposed implementation
3. User approves
4. Agent (Skill layer) writes new code for the Python engine
5. New capability becomes available for all future analyses

Example flow:
```
[Capability Expansion Request]
Need: Sentiment analysis for user reviews
Reason: Currently can only count star ratings, cannot identify specific pain points
Proposal: Add keyword extraction logic to engine/collectors/reviews.py
```

This means the agent's capability set grows over time, driven by actual operational needs rather than speculative features.

## Interaction Model

### Full-Auto + Approval

- Agent autonomously performs all analysis and decision-making
- Generates concrete action plans (code PRs, ASO copy, marketing plans)
- User only responsible for:
  - Approving/rejecting plans
  - Executing actions AI cannot do (App Store submission, payments, etc.)
  - Updating program.md when strategy direction changes

### Approval Flow

```
Agent generates plan → writes to actions/pending.md
User runs /appagent → sees pending plans first (highest priority)
User approves/rejects/modifies
If approved:
  - Code changes → agent executes directly
  - Human tasks → moved to actions/approved/ with instructions
  - Experiment starts → tracked in experiments/active.json
```

### Human Task Queue

For actions the agent cannot execute:
```markdown
## Pending Human Tasks

### [HIGH] Submit App Store Update
- Version 2.1.0 with AI filter feature is ready
- Build has been created and tested
- Action needed: Submit via App Store Connect
- Deadline: Before 2026-04-15 (keyword trend window)

### [MEDIUM] Update App Store Screenshots
- New screenshots generated at: .appagent/assets/screenshots/
- Action needed: Upload to App Store Connect
- Reason: Current screenshots don't show new AI filter feature
```

## Storage Strategy

### Phase 1: File Storage (Starting Point)
- JSON files for structured data (metrics, experiments, experience)
- JSONL for append-only logs (experiment history)
- Markdown for human-readable outputs (reports, pending actions)
- Git-friendly: all changes are diffable and trackable

### Future Migration Path
- If query performance becomes an issue → migrate to SQLite (single file, zero config)
- Migration is straightforward: same `.appagent/` directory, `data.db` replaces JSON files
- No architectural changes needed, only the `store/` module changes

## Development Phases

### Phase 1: Skill Foundation (~1 week)
- `/appagent` Skill with smart main loop
- program.md reading and interpretation
- Competitor analysis via browser
- Code analysis and suggestions
- Human task queue (actions/pending.md)
- Basic state tracking (state.json)

### Phase 2: Python Data Engine (~2 weeks)
- App Store Connect API integration
- Automated data collection (collectors/)
- Trend analysis and anomaly detection
- Experiment tracking system
- CLI tool (appagent collect/daemon)
- launchd scheduled tasks

### Phase 3: Self-Improvement System (~1 week)
- Experience database (local + global)
- Cross-app experience migration
- Capability expansion workflow
- Budget ROI tracking
- Milestone auto-detection and stage transitions

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Hybrid (Skill + Python) | Best of both: no API cost for LLM, full data automation |
| Runtime | Local Mac | Zero hosting cost, user has dev machine always on |
| Storage | File-based (JSON/JSONL/MD) | Simple, git-friendly, sufficient for current scale |
| Data source | App Store Connect API Key | Free, fully automated, official |
| LLM interaction | Claude Code subscription | No additional API cost |
| Scheduling | macOS launchd | Native, reliable, no extra dependencies |
| Cross-layer communication | File system (.appagent/) | Zero complexity, both layers read/write files |
