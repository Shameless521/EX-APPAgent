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

**Skill Layer:**
- Runs inside Claude Code, uses existing subscription (no API key needed)
- Reads project code, generates action plans, writes code changes
- Reads analysis data from Python engine via `.appagent/` directory
- Handles all LLM-powered reasoning, decision-making, and code generation

**Python Engine:**
- Pure Python, no LLM calls required
- Handles data collection, storage, trend analysis, experiment tracking
- Runs via cron/launchd for scheduled collection (daily)
- Communicates with Skill layer through `.appagent/` file directory

### Data Exchange & File Ownership

Both layers communicate through the `.appagent/` directory within each app project. To prevent concurrent write corruption, each file has a **single owner** — only the owner may write, the other layer is read-only.

| File/Directory | Write Owner | Reader |
|---|---|---|
| `program.md` | Human only | Skill Layer |
| `state.json` | Skill Layer | Python Engine |
| `health.json` | Python Engine | Skill Layer |
| `data/*` (metrics, competitors, aso) | Python Engine | Skill Layer |
| `experiments/log.jsonl` | Skill Layer (verdict) | Python Engine |
| `experiments/active.json` | Skill Layer | Python Engine |
| `experiments/pre-calc/` | Python Engine | Skill Layer |
| `insights/*` | Skill Layer | Python Engine |
| `actions/*` | Skill Layer | Both |
| `reports/*` | Skill Layer | Human |

**Atomic write protocol:** All file writes use the temp-file-then-rename pattern (`os.replace()` in Python, write-to-temp + rename in Skill layer) to prevent partial-write corruption.

## program.md — The Core Directive

Each app project contains a `program.md` at the root. This is the only file the human writes. The agent reads it but never modifies it. Changing this file is how the human "programs" the agent's behavior.

**Important:** `program.md` contains only static configuration (human intent). All dynamic data (current metrics, conversion rates, stage progress) lives in `state.json`, which the agent maintains automatically.

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
data_sources:
  - Primary: third-party analytics platforms (e.g., Sensor Tower, App Annie, 七麦数据, etc.)
  - Secondary: Skill layer browser research for deep-dive analysis

# Guardrails
## System-enforced (hard-coded in Python engine, cannot be bypassed)
never_system:
  - Exceed daily_limit in a single day
  - Write files outside .appagent/ and engine/ directories
  - Make network requests to non-whitelisted domains (in capability expansion)

## LLM-enforced (prompt constraints, best-effort)
never_llm:
  - False advertising or fake reviews
  - Copy competitor UI designs
  - Collect or upload user data without authorization
  - Modify multiple monetization parameters simultaneously

caution:
  - Price reductions require at least 7 days of data support
  - Removing existing features requires confirming no active users
  - New permissions (beyond core functionality) require human approval

# Experiments
rules:
  - Single variable per experiment
  - Minimum observation period: 7 days
  - Significance: change must exceed 2x historical standard deviation (not just >5%)
  - 2 consecutive failures on same approach → pivot direction
  - Each experiment must log confounding_factors (external events during observation)
log: .appagent/experiments/log.jsonl

# Current Focus
priorities:
  1. Priority task 1
  2. Priority task 2
  3. Priority task 3
```

### Design Principles

- **Static vs dynamic separation**: `program.md` = human intent (goals, constraints, strategy). `state.json` = current reality (metrics, stage, conversion rates). Agent merges both at runtime.
- **Milestone-driven**: Not a single leap to $20/day. Each milestone unlocks new strategy space (higher budgets, more aggressive experiments).
- **Guardrails are tiered**: System-enforced guardrails are hard-coded checks that cannot be bypassed. LLM-enforced guardrails are prompt constraints with best-effort reliability.
- **Scientific experiments**: Single-variable principle + minimum observation period + statistical significance against historical variance. Requires logging confounding factors for better attribution.
- **Aligned with autoresearch**: program.md is the human's only file. The agent reads it, never writes it. Modifying this file is "programming" the agent.

## state.json — Dynamic State

All dynamic data lives here. Maintained by the Skill layer, read by both layers.

```json
{
  "stage": {
    "current": "from_0.5_to_1",
    "milestone_target": 1.0,
    "milestone_unlocks": "small ad spend"
  },
  "latest_metrics": {
    "date": "2026-04-12",
    "daily_revenue": 0.5,
    "daily_downloads": 30,
    "rating": 4.6,
    "active_subscriptions": 5
  },
  "current_conversion": {
    "download_to_register": 0.65,
    "register_to_trial": 0.12,
    "trial_to_paid": 0.08
  },
  "last_analysis": "2026-04-12T08:30:00",
  "last_analysis_summary": "Routine: pushed ASO keyword optimization",
  "active_experiments_count": 1,
  "total_experiments": 5,
  "experience_entries": 12
}
```

## Project Directory Structure

### Per-App Structure

```
MyApp/
├── program.md                      # Human-written agent directive (static config)
├── .appagent/
│   ├── state.json                  # Dynamic state (Skill writes, both read)
│   ├── health.json                 # Python engine health status
│   ├── data/                       # Python engine writes, Skill reads
│   │   ├── metrics/
│   │   │   └── 2026-04-12.json     # Daily: downloads, revenue, ratings, rankings
│   │   ├── competitors/
│   │   │   └── vsco.json           # Competitor profile from third-party platforms
│   │   └── aso/
│   │       └── keywords.json       # Keyword rankings and search volume
│   ├── experiments/
│   │   ├── log.jsonl               # All experiment records (Skill writes)
│   │   ├── active.json             # Currently running experiments (Skill writes)
│   │   └── pre-calc/              # Python pre-calculations for pending verdicts
│   │       └── exp_001.json        # Metric snapshots for experiment judgment
│   ├── insights/                   # Skill writes
│   │   ├── experience-aso.json     # ASO-related experience
│   │   ├── experience-pricing.json # Pricing-related experience
│   │   ├── experience-growth.json  # Growth-related experience
│   │   └── experience-product.json # Product/feature-related experience
│   ├── actions/
│   │   ├── pending/               # Each plan is a separate file
│   │   │   └── 2026-04-12-aso-keyword.md
│   │   ├── approved/              # Approved, ready to execute
│   │   ├── rejected/             # Rejected with reason (feeds into experience)
│   │   └── history/              # Completed plans archive
│   └── reports/
│       └── weekly-summary.md      # Weekly summary report
├── src/                           # App source code (existing)
└── ...
```

### Global Structure

```
~/.appagent/
├── global-insights/               # Cross-app universal experience
│   ├── experience-aso.json
│   ├── experience-pricing.json
│   ├── experience-growth.json
│   └── experience-product.json
├── config.json                    # Global settings (API keys, defaults)
├── apps.json                      # Registry of all managed apps
└── privacy.json                   # Data sharing settings (local-only by default)
```

**Experience flow**: When the agent writes an insight to the per-app `insights/`, it evaluates whether the insight has cross-app applicability. If yes, it also syncs to `~/.appagent/global-insights/`. When analyzing any app, the agent reads both local and global experience, loading only the relevant category file (e.g., only `experience-aso.json` for an ASO task).

**Privacy**: Global experience library is strictly local. `privacy.json` explicitly defaults to `{"share_externally": false}`. No data is ever synced to external services.

### health.json — Engine Health Status

Written by the Python engine, read by the Skill layer before every analysis cycle.

```json
{
  "python_engine": {
    "last_run": "2026-04-12T06:00:00",
    "last_success": "2026-04-12T06:00:00",
    "status": "ok",
    "errors": []
  },
  "data_freshness": {
    "metrics": "2026-04-12",
    "competitors": "2026-04-11",
    "aso": "2026-04-12"
  },
  "api_status": {
    "appstore_connect": "ok",
    "google_play": "ok"
  }
}
```

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
2. Read health.json             → Check Python engine status and data freshness
   ├─ If data stale (>48h)      → Warn user, suggest checking engine
   └─ If engine error           → Show error, offer manual collect
3. Read state.json              → Current stage and last analysis
4. Read data/metrics/           → Latest data from Python engine
5. Read experiments/            → Pre-calc results + active experiments
6. Read insights/ (relevant)    → Historical experience (local + global, by category)
7. Auto-determine priority      → What's most important right now?
8. Analyze + decide             → Generate action plan
9. Write actions/pending/       → Each plan as separate file, await approval
10. Update state.json           → Record this analysis cycle
```

The loop never changes. The data changes. This is the harness.

### Priority Determination

The agent automatically selects the highest-priority action:

| Priority | Condition | Action |
|----------|-----------|--------|
| 1. Milestone | A milestone has been reached | Celebrate, update stage, unlock new strategies |
| 2. Urgent | Pending actions awaiting approval | Present for review |
| 3. Experiment | An experiment's observation period ended | LLM judges keep/discard using Python pre-calc data |
| 4. Anomaly | Metrics show abnormal change (>2x historical std dev) | Diagnose cause, generate response plan |
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
│   ├── googleplay.py            # Google Play Developer API
│   ├── reviews.py               # User review fetching and parsing
│   ├── aso.py                   # Keyword ranking tracking
│   └── competitor.py            # Third-party platform data (Sensor Tower, 七麦, etc.)
├── analyzer/
│   ├── trends.py                # Trend calculation (WoW, MoM, anomaly detection, std dev)
│   └── experiment.py            # Experiment pre-calculation (metrics delta, not verdict)
├── store/
│   ├── writer.py                # Atomic write to .appagent/data/ (temp file + rename)
│   └── experience.py            # Experience library management (local + global, by category)
├── health.py                    # Write health.json after each run
├── guardrails.py                # System-enforced guardrails (budget limits, file access)
├── scheduler.py                 # Local cron/launchd wrapper
├── extensions/                  # Agent-written capability extensions (sandboxed)
│   └── README.md                # Extension development constraints
└── cli.py                       # CLI entry point
```

### CLI Commands

```bash
appagent collect                 # Manual one-time data collection
appagent collect --app PhotoCraft # Collect for specific app
appagent daemon                  # Start scheduled collection (via launchd)
appagent daemon stop             # Stop scheduled collection
appagent health                  # Check engine health and data freshness
```

### Data Collection

- **App Store Connect API**: Revenue, downloads, subscriptions, ratings — via API Key (free with Apple Developer account). Note: sales data is delayed 1-2 days; collection runs once daily (early morning, fetching T-2 data).
- **Google Play Developer API**: Same data for Android apps (requires Service Account setup).
- **User Reviews**: Fetched via store APIs, can be collected more frequently (2-3x daily).
- **ASO Keywords**: Track ranking changes for target keywords.
- **Competitor Data**: Sourced from third-party analytics platforms (Sensor Tower, App Annie, 七麦数据, etc.). Skill layer browser research for deep-dive analysis when needed. No direct App Store scraping.

Collection frequency: Once daily for revenue/download metrics (due to App Store data delay), 2-3x daily for reviews and ASO data.

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
  "historical_std_dev": 5.2,
  "delta_pct": 40,
  "exceeds_2x_std_dev": true,
  "confounding_factors": ["competitor Dazz had a server outage on 04-08"],
  "verdict": "keep",
  "verdict_reasoning": "Download increase (40%) far exceeds 2x std dev (34.7%). Dazz outage may have contributed ~5-10% but core improvement is real.",
  "insight": "film camera is an effective keyword — high search volume, medium competition",
  "insight_category": "aso",
  "cross_app_applicable": true
}
```

**Experiment pre-calculation** (`experiments/pre-calc/exp_001.json`):

Written by Python engine when an experiment's observation period ends. Contains raw numbers only — no verdict.

```json
{
  "id": "exp_001",
  "observation_complete": true,
  "metric_before": {"daily_downloads": 30},
  "metric_after": {"daily_downloads": 42},
  "delta_pct": 40,
  "historical_std_dev": 5.2,
  "exceeds_2x_std_dev": true,
  "daily_breakdown": [28, 35, 40, 45, 42, 48, 44],
  "external_events_detected": ["competitor Dazz app unavailable 04-08 to 04-09"]
}
```

## Self-Improvement System

### Strategy Evolution (Experience Accumulation)

Every experiment follows the autoresearch cycle with clear role separation:

1. Agent (Skill layer) proposes a change (hypothesis), writes to `experiments/active.json`
2. Change is implemented (after user approval)
3. Python engine tracks metrics for the observation period, writes daily snapshots
4. At period end, Python engine writes pre-calculation to `experiments/pre-calc/` (raw numbers, no verdict)
5. Next time user triggers `/appagent`, Skill layer (LLM) makes the final verdict:
   - Reads pre-calc data (quantitative)
   - Considers confounding factors (qualitative)
   - Judges **keep** or **discard** with reasoning
   - Example: "Downloads dropped 10% but competitor ran a massive promo campaign — strategy itself is sound, verdict: keep"
6. Insight extracted and written to relevant experience category file
7. If cross-app applicable, synced to global experience

**Why LLM judges, not Python**: Pure rule-based judgment (delta > 5%) cannot account for context. A 10% drop during a competitor's fire-sale is not the same as a 10% drop in normal conditions. The LLM reads the numbers AND the context to make nuanced decisions.

Over time, the agent builds a growing knowledge base of what works and what doesn't, across all apps. When analyzing a new app, it draws on this accumulated wisdom, loading only the relevant experience category.

### Capability Expansion (Learning New Skills)

When the agent identifies a capability gap:
1. Agent generates a "capability expansion request" in `actions/pending/`
2. Request includes: what's needed, why, proposed implementation, and **full code diff**
3. Automatic safety checks run against the diff:
   - No file access outside `.appagent/` and `engine/` directories
   - No network requests to non-whitelisted domains
   - No access to user home directory sensitive files (~/.ssh, ~/.aws, etc.)
4. User reviews the full diff and approves
5. Agent (Skill layer) writes new code to `engine/extensions/`
6. New code runs in dry-run mode first (mock output, no real execution)
7. If dry-run passes, capability is activated for real use

Example flow:
```markdown
## Capability Expansion Request

**Need:** Sentiment analysis for user reviews
**Reason:** Currently can only count star ratings, cannot identify specific pain points
**Proposal:** Add keyword extraction logic to engine/extensions/review_sentiment.py

### Code Diff
[full code shown here, not just description]

### Safety Check Results
- File access: ✅ Only writes to .appagent/data/
- Network: ✅ No external requests
- Sensitive paths: ✅ None accessed
```

This means the agent's capability set grows over time, driven by actual operational needs rather than speculative features.

## Action Plan Lifecycle

### Plan File Format

Each plan is a separate file in `actions/pending/`:

```markdown
# Plan: ASO Keyword Optimization

**ID:** plan-2026-04-12-aso-keyword
**Created:** 2026-04-12T08:30:00
**Type:** aso_optimization
**Priority:** high

## Analysis
[Data-driven reasoning for this plan]

## Proposed Actions
1. Add keywords: "film camera", "vintage filter"
2. Update subtitle to include "AI-powered"

## Expected Impact
- Keyword coverage: 15 → 25
- Estimated download increase: 20-30%

## Experiment Setup
- Variable: ASO keywords
- Observation period: 7 days
- Success metric: daily downloads

## Decision
- Status: pending
- Approved by: [user]
- Rejection reason: [if rejected]
- Do not retry: [yes/no]
```

### Lifecycle

```
Agent generates plan → actions/pending/plan-xxx.md (status: pending)
User triggers /appagent → sees pending plans (priority 2)
User decides:
  ├─ Approve → move to actions/approved/, start experiment tracking
  ├─ Reject → move to actions/rejected/, record reason
  │           rejection reason synced to experience as negative signal
  │           if "do not retry: yes", agent will not propose similar plans
  └─ Modify → user edits plan, agent re-evaluates and re-submits
```

**Key rule:** Agent never overwrites existing pending plans. Each plan is an independent file. Old unreviewed plans persist until the user deals with them.

## Cold Start Protocol

No extra command needed. When `/appagent` is triggered, the harness loop automatically detects and handles cold start as part of its normal flow:

```
Harness Step 1: Read program.md
├─ No program.md? → Generate template, ask user to fill in, stop here
└─ Has program.md → continue

Harness Step 2: Read health.json
├─ No .appagent/ directory? → Auto-create full directory structure
│   ├─ Initialize state.json (empty metrics, stage = "cold_start")
│   ├─ Initialize health.json
│   ├─ Register app in ~/.appagent/apps.json
│   └─ Check global config for API keys, prompt if missing
└─ Has .appagent/ → continue normally

Harness Step 3-6: Read data
├─ No data yet? → Enter cold start mode (see below)
└─ Has data → continue normally
```

### Cold Start Mode

When the harness detects empty data directories, it automatically shifts to cold start behavior instead of normal analysis:

- **Metrics:** Skip quantitative analysis, note "no historical data yet"
- **Experiments:** Nothing to judge, skip
- **Insights:** Load global insights from other apps (cross-app experience still available)
- **Priority:** Override to cold start sequence:
  1. Analyze source code to understand what the app does
  2. Use browser to research competitors from program.md watch_list
  3. Generate initial strategy recommendations based on global experience + competitor analysis
  4. Suggest first experiment
  5. Trigger first data collection (Python engine)

The agent is useful from day one. After the first data collection completes, subsequent `/appagent` runs enter the normal harness loop automatically. No mode switching needed — the harness adapts based on what data is available.

## Interaction Model

### Full-Auto + Approval

- Agent autonomously performs all analysis and decision-making
- Generates concrete action plans (code PRs, ASO copy, marketing plans)
- User only responsible for:
  - Approving/rejecting plans (with rejection reasons)
  - Executing actions AI cannot do (App Store submission, payments, etc.)
  - Updating program.md when strategy direction changes

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
- Experience files split by category (aso, pricing, growth, product) to keep individual files small
- Git-friendly: all changes are diffable and trackable

### Future Migration Path
- If query performance becomes an issue → migrate to SQLite (single file, zero config)
- Migration is straightforward: same `.appagent/` directory, `data.db` replaces JSON files
- No architectural changes needed, only the `store/` module changes

## Development Phases

### Phase 1: Skill Foundation (~1 week)
- `/appagent` Skill with smart main loop (harness)
- program.md reading and interpretation
- state.json management
- Cold start protocol (auto-detected in harness loop)
- Competitor analysis via browser + third-party platforms
- Code analysis and suggestions
- Action plan lifecycle (pending → approved/rejected → history)
- Basic experience tracking

### Phase 2: Python Data Engine (~2 weeks)
- App Store Connect API integration (with data delay awareness)
- Google Play Developer API integration
- Automated data collection (collectors/)
- Third-party competitor data integration
- Trend analysis and anomaly detection (with historical std dev)
- Experiment pre-calculation system
- health.json engine status reporting
- System-enforced guardrails (guardrails.py)
- CLI tool (appagent collect/daemon/health)
- launchd scheduled tasks

### Phase 3: Self-Improvement System (~1 week)
- Experience database by category (local + global)
- Cross-app experience migration with applicability judgment
- Capability expansion workflow (with safety checks and dry-run)
- Budget ROI tracking
- Milestone auto-detection and stage transitions

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Hybrid (Skill + Python) | Best of both: no API cost for LLM, full data automation |
| Runtime | Local Mac | Zero hosting cost, user has dev machine always on |
| Storage | File-based (JSON/JSONL/MD) | Simple, git-friendly, sufficient for current scale |
| File writes | Atomic (temp + rename) | Prevents concurrent write corruption |
| File ownership | Single writer per file | Eliminates race conditions between layers |
| Data source (own apps) | App Store Connect API Key | Free, fully automated, official (1-2 day delay) |
| Data source (competitors) | Third-party platforms | Sensor Tower, 七麦数据, etc. — reliable and comprehensive |
| LLM interaction | Claude Code subscription | No additional API cost |
| Experiment verdict | Python pre-calc + LLM judgment | Quantitative rigor + contextual reasoning |
| Experience storage | Category-split files | Prevents single-file bloat, enables selective loading |
| Scheduling | macOS launchd | Native, reliable, no extra dependencies |
| Guardrails | Two-tier (system + LLM) | Critical constraints hard-coded, soft constraints prompt-based |
| Cross-layer communication | File system (.appagent/) | Zero complexity, both layers read/write files |
| Privacy | Local-only, no external sync | User's business data never leaves their machine |
