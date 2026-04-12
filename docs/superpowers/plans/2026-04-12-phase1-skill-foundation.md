# EX-APPAgent Phase 1: Skill Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `/appagent` Claude Code Skill with smart harness loop, cold start protocol, competitor analysis via browser, action plan lifecycle, and state management — usable from day one without the Python engine.

**Architecture:** Single-entry-point Skill (`/appagent`) that reads `program.md` + `state.json`, auto-determines priority, generates action plans, and manages the approval lifecycle. Modular design: main orchestrator skill delegates to module files loaded via `Read` tool and sub-agents dispatched via `Agent` tool. Follows the same plugin pattern as the user's existing EX-RequireAgent.

**Tech Stack:** Claude Code Skill (Markdown), JSON for state management, Claude Code Plugin system

---

## File Structure

```
EX-APPAgent/
├── .claude-plugin/
│   └── plugin.json                     # Plugin metadata
├── .claude/
│   └── commands/
│       └── appagent.md                 # Main skill entry point (/appagent)
├── modules/
│   ├── harness-loop.md                 # Core harness loop logic (9 steps)
│   ├── cold-start.md                   # Cold start detection and initialization
│   ├── priority-engine.md              # Priority determination (5 levels)
│   ├── action-lifecycle.md             # Pending → approved/rejected → history
│   └── state-manager.md               # state.json read/write protocol
├── agents/
│   ├── analyst.md                      # Data analysis and strategy generation
│   ├── competitor-researcher.md        # Competitor analysis via browser
│   └── code-operator.md               # Code analysis and modification
├── templates/
│   ├── program-template.md             # Template for new app's program.md
│   ├── state-initial.json              # Initial state.json structure
│   └── health-initial.json             # Initial health.json structure
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-04-12-appagent-design.md
        └── plans/
            └── 2026-04-12-phase1-skill-foundation.md
```

---

### Task 1: Plugin Registration

**Files:**
- Create: `.claude-plugin/plugin.json`

- [ ] **Step 1: Create plugin metadata**

```json
{
  "name": "ex-appagent",
  "description": "Autonomous app management agent — feature iteration, marketing, competitor analysis, and revenue optimization with self-improving harness loop",
  "version": "0.1.0",
  "author": {
    "name": "MonkCoding"
  }
}
```

- [ ] **Step 2: Verify plugin directory structure**

Run: `ls -la /Library/MonkCoding/git_Project/EX-APPAgent/.claude-plugin/`
Expected: `plugin.json` exists

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "chore: initialize EX-APPAgent plugin structure"
```

---

### Task 2: Templates — program.md, state.json, health.json

These templates are used during cold start to initialize a new app's `.appagent/` directory.

**Files:**
- Create: `templates/program-template.md`
- Create: `templates/state-initial.json`
- Create: `templates/health-initial.json`

- [ ] **Step 1: Create program.md template**

```markdown
# Identity
name: [APP_NAME]
platform: [e.g., iOS + Android (Flutter)]
tech_stack: [e.g., Flutter 3.x / Dart / Firebase]
positioning: [One-line description: what the app is and who it's for]
differentiator: [What makes this app different from competitors]
app_store_id: [e.g., com.example.appname]
store_url: [e.g., https://apps.apple.com/app/id123456]

# Target
north_star: Daily pure revenue $20
milestones:
  - $1/day → monetization model validated (unlock: small ad spend)
  - $5/day → stable growth phase (unlock: increase daily budget to $10)
  - $20/day → target achieved (unlock: consider new feature lines)

# Users
primary: [Target demographic and behavior description]
pain_points:
  - [Pain point 1]
  - [Pain point 2]
willingness_to_pay: [Low / Medium / High]
discovery_channels: [Where users find this type of app]

# Monetization
model: [freemium + subscription / paid / ad-supported]
pricing:
  - Free tier: [what's included]
  - Paid tier: [price and what's included]
  - One-time purchases: [items and prices]

# Budget
daily_limit: $5-10
min_roas: 1.5
preferred_channels:
  - Priority: [free channels]
  - Secondary: [paid channels, requires data support]
  - Not now: [channels not worth the budget yet]

# Competitors
watch_list:
  - [CompetitorA] (priority) — focus: [what to watch]
  - [CompetitorB] — focus: [what to watch]
analysis_dimensions:
  - Feature comparison / pricing / ASO keywords / review sentiment / update frequency
data_sources:
  - Primary: third-party analytics platforms
  - Secondary: Skill layer browser research

# Guardrails
## System-enforced
never_system:
  - Exceed daily_limit in a single day
  - Write files outside .appagent/ and engine/ directories

## LLM-enforced
never_llm:
  - False advertising or fake reviews
  - Copy competitor UI designs
  - Collect or upload user data without authorization
  - Modify multiple monetization parameters simultaneously

caution:
  - Price reductions require at least 7 days of data support
  - Removing existing features requires confirming no active users
  - New permissions require human approval

# Experiments
rules:
  - Single variable per experiment
  - Minimum observation period: 7 days
  - Significance: change must exceed 2x historical standard deviation
  - 2 consecutive failures on same approach → pivot direction
  - Each experiment must log confounding_factors
log: .appagent/experiments/log.jsonl

# Current Focus
priorities:
  1. [Priority task 1]
  2. [Priority task 2]
  3. [Priority task 3]
```

- [ ] **Step 2: Create state-initial.json**

```json
{
  "stage": {
    "current": "cold_start",
    "milestone_target": 1.0,
    "milestone_unlocks": "small ad spend"
  },
  "latest_metrics": {
    "date": null,
    "daily_revenue": 0,
    "daily_downloads": 0,
    "rating": null,
    "active_subscriptions": 0
  },
  "current_conversion": {
    "download_to_register": null,
    "register_to_trial": null,
    "trial_to_paid": null
  },
  "last_analysis": null,
  "last_analysis_summary": null,
  "active_experiments_count": 0,
  "total_experiments": 0,
  "experience_entries": 0
}
```

- [ ] **Step 3: Create health-initial.json**

```json
{
  "python_engine": {
    "last_run": null,
    "last_success": null,
    "status": "not_configured",
    "errors": []
  },
  "data_freshness": {
    "metrics": null,
    "competitors": null,
    "aso": null
  },
  "api_status": {
    "appstore_connect": "not_configured",
    "google_play": "not_configured"
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add templates/
git commit -m "feat: add templates for program.md, state.json, and health.json"
```

---

### Task 3: State Manager Module

Handles reading/writing state.json with atomic write protocol. Referenced by the main skill and other modules.

**Files:**
- Create: `modules/state-manager.md`

- [ ] **Step 1: Create state-manager.md**

```markdown
# State Manager

## Reading State

1. Read `.appagent/state.json` using the Read tool
2. Parse the JSON content
3. Return the parsed state object for use in the harness loop

If the file does not exist, return `null` — the harness loop will trigger cold start.

## Writing State

State writes happen at the end of the harness loop (Step 10) and when milestones are reached.

**Atomic write protocol:**
1. Write the updated JSON to `.appagent/state.tmp.json` using Write tool
2. Run `mv .appagent/state.tmp.json .appagent/state.json` via Bash tool
3. This ensures readers never see a partially-written file

**Fields to update after each analysis cycle:**
- `last_analysis`: current ISO timestamp
- `last_analysis_summary`: one-line description of what was done
- `active_experiments_count`: count of experiments in active.json
- `total_experiments`: count of lines in experiments/log.jsonl
- `experience_entries`: sum of entries across all experience files

**Fields to update on milestone reached:**
- `stage.current`: new stage identifier
- `stage.milestone_target`: next milestone value
- `stage.milestone_unlocks`: what the next milestone unlocks

**Fields to update when new metrics arrive (from Python engine data):**
- `latest_metrics.*`: copy latest values from data/metrics/ files
- `current_conversion.*`: update if conversion data is available

## Milestone Detection

Compare `latest_metrics.daily_revenue` against `stage.milestone_target`:
- If revenue >= milestone_target for 3 consecutive days → milestone reached
- Update stage fields to next milestone
- Return `milestone_reached: true` to the harness loop for priority override
```

- [ ] **Step 2: Commit**

```bash
git add modules/state-manager.md
git commit -m "feat: add state manager module with atomic write protocol"
```

---

### Task 4: Cold Start Module

Handles first-time initialization when no `.appagent/` directory exists.

**Files:**
- Create: `modules/cold-start.md`

- [ ] **Step 1: Create cold-start.md**

```markdown
# Cold Start Protocol

## Detection

Cold start is detected when ANY of these are true:
- `.appagent/` directory does not exist
- `.appagent/state.json` does not exist
- `state.json` has `stage.current` = `"cold_start"`

## Phase A: Ensure program.md Exists

1. Use Glob to check if `program.md` exists in the project root
2. If NO program.md:
   - Read `templates/program-template.md` from the plugin directory
   - Write it to the project root as `program.md`
   - Tell the user: "I've created a `program.md` template in your project root. Please fill in the details about your app — especially Identity, Target, Users, Monetization, and Competitors. Then run `/appagent` again."
   - **STOP HERE** — do not proceed until program.md is filled in
3. If program.md EXISTS but contains unfilled placeholders (e.g., `[APP_NAME]`):
   - Tell the user which sections still need to be filled in
   - **STOP HERE**

## Phase B: Initialize .appagent/ Directory

1. Create the full directory structure:
   ```
   mkdir -p .appagent/data/metrics
   mkdir -p .appagent/data/competitors
   mkdir -p .appagent/data/aso
   mkdir -p .appagent/experiments/pre-calc
   mkdir -p .appagent/insights
   mkdir -p .appagent/actions/pending
   mkdir -p .appagent/actions/approved
   mkdir -p .appagent/actions/rejected
   mkdir -p .appagent/actions/history
   mkdir -p .appagent/reports
   ```

2. Copy templates:
   - Read `templates/state-initial.json` → write to `.appagent/state.json`
   - Read `templates/health-initial.json` → write to `.appagent/health.json`

3. Register app in global config:
   - Read `~/.appagent/apps.json` (create if not exists)
   - Add entry: `{"name": "<from program.md>", "path": "<current project path>", "registered_at": "<ISO timestamp>"}`
   - Write back using atomic write

4. Add `.appagent/` to `.gitignore` if not already present

## Phase C: Cold Start Analysis

Since there's no historical data, the harness loop enters cold start mode:

1. **Analyze source code**: Read key source files to understand what the app does, its current features, tech stack
2. **Read global experience**: Load `~/.appagent/global-insights/` files if they exist (cross-app experience from other apps)
3. **Competitor research**: Use the competitor-researcher agent to analyze competitors from program.md watch_list via browser
4. **Generate initial strategy**: Based on code analysis + global experience + competitor research, generate:
   - Initial assessment of the app's strengths and weaknesses
   - Top 3 recommended first actions
   - Suggested first experiment
5. Write recommendations to `actions/pending/` as plan files
6. Update `state.json`: set `stage.current` to first milestone stage (e.g., `"from_0_to_1"`)

Tell the user: "Cold start complete. I've analyzed your app and generated initial recommendations. Here's what I found: [summary]. Review the pending plans and let me know which to proceed with."
```

- [ ] **Step 2: Commit**

```bash
git add modules/cold-start.md
git commit -m "feat: add cold start module with auto-initialization"
```

---

### Task 5: Priority Engine Module

Determines what the agent should focus on based on current state.

**Files:**
- Create: `modules/priority-engine.md`

- [ ] **Step 1: Create priority-engine.md**

```markdown
# Priority Engine

## Input

The priority engine receives:
- `state`: parsed state.json
- `health`: parsed health.json (may be null in Phase 1)
- `pending_plans`: list of files in actions/pending/
- `active_experiments`: parsed experiments/active.json (may be empty)
- `latest_metrics`: most recent metrics file from data/metrics/ (may be null)
- `program`: parsed program.md

## Priority Determination

Evaluate conditions in order. The FIRST matching condition determines the action.

### Priority 1: Milestone Reached

**Condition:** `latest_metrics.daily_revenue >= stage.milestone_target` for 3+ consecutive days

**Action:**
- Announce milestone achievement with congratulations
- Update stage to next milestone (use state-manager module)
- Present newly unlocked strategies (from program.md milestones section)
- Suggest updated Current Focus priorities

### Priority 2: Pending Plans Awaiting Review

**Condition:** `actions/pending/` directory contains one or more plan files

**Action:**
- Present each pending plan with a summary
- For each plan, ask user: Approve / Reject / Modify
- On approve: move file to `actions/approved/`, begin execution or experiment tracking
- On reject: ask for rejection reason, move file to `actions/rejected/`, extract negative insight and write to relevant experience file
- On modify: present plan for editing, re-submit

### Priority 3: Experiment Observation Complete

**Condition:** An experiment in `experiments/active.json` has `observation_end_date <= today`

**Action:**
- Read experiment details and pre-calc data (if available from Python engine)
- If no pre-calc (Phase 1 — no Python engine yet):
  - Check if user can provide current metrics manually
  - Or read any available data from data/metrics/
- Make verdict judgment (keep/discard) with reasoning
- Write experiment result to `experiments/log.jsonl`
- Extract insight, write to relevant `insights/experience-{category}.json`
- If cross-app applicable, sync to `~/.appagent/global-insights/`
- Remove from `experiments/active.json`

### Priority 4: Data Anomaly Detected

**Condition:** Latest metrics show >2x standard deviation change from 7-day rolling average

**Note:** In Phase 1 without Python engine, this detection is limited. The agent checks available metric files manually. Full anomaly detection comes in Phase 2.

**Action:**
- Identify which metric(s) changed abnormally
- Analyze possible causes (check competitor changes, recent experiments, external events)
- Generate response plan in `actions/pending/`

### Priority 5: Routine — Push Current Focus

**Condition:** None of the above triggered

**Action:**
- Read `Current Focus` priorities from program.md
- Assess progress on each priority using available data
- Select the most impactful next action
- Generate a plan in `actions/pending/`
- Possible actions include:
  - ASO keyword research and optimization suggestions
  - Code analysis for feature improvements
  - Competitor deep-dive via browser
  - Conversion funnel analysis and improvement suggestions

## Output

Return to the harness loop:
- `priority_level`: which priority triggered (1-5)
- `priority_label`: human-readable label ("Milestone Reached", "Pending Plans", etc.)
- `action_taken`: what was done
- `plans_generated`: count of new plans in pending/
```

- [ ] **Step 2: Commit**

```bash
git add modules/priority-engine.md
git commit -m "feat: add priority engine module with 5-level determination"
```

---

### Task 6: Action Lifecycle Module

Manages the full lifecycle of action plans: creation, approval, rejection, archival.

**Files:**
- Create: `modules/action-lifecycle.md`

- [ ] **Step 1: Create action-lifecycle.md**

```markdown
# Action Lifecycle

## Plan File Format

Each plan is a Markdown file in `actions/pending/`. Filename format: `YYYY-MM-DD-{short-description}.md`

```markdown
# Plan: {Title}

**ID:** plan-{YYYY-MM-DD}-{short-id}
**Created:** {ISO timestamp}
**Type:** {aso_optimization | feature_development | pricing_change | marketing | bug_fix | experiment}
**Priority:** {high | medium | low}
**Requires Human Action:** {yes | no}

## Analysis
{Data-driven reasoning for this plan. What data led to this recommendation.}

## Proposed Actions
1. {Specific action 1}
2. {Specific action 2}

## Expected Impact
- {Metric}: {current} → {expected} ({change}%)

## Experiment Setup
- Variable: {what's being changed}
- Observation period: {N} days
- Success metric: {which metric to watch}
- Baseline: {current value}

## Human Tasks (if any)
- [ ] {Task requiring human action, e.g., "Submit to App Store"}

## Decision
- Status: pending
- Decided by: {user}
- Decision date: {filled on decision}
- Rejection reason: {filled if rejected}
- Do not retry similar: {yes/no, filled if rejected}
```

## Creating Plans

When generating a plan:
1. Determine plan type from the analysis context
2. Fill all fields — no placeholders or TBDs
3. Write to `actions/pending/{YYYY-MM-DD}-{short-description}.md`
4. Log creation in state.json via state-manager module

## Presenting Plans for Review

When pending plans exist (Priority 2):
1. Read all files in `actions/pending/`
2. Sort by priority (high → medium → low)
3. Present each plan with a concise summary:
   - Title, type, priority
   - Key reasoning (1-2 sentences from Analysis)
   - Expected impact
   - Whether human action is required
4. Ask for decision on each: **Approve / Reject / Modify / Skip**

## Approval Flow

**On Approve:**
1. Update plan's Decision section: status = approved, decision date = now
2. Move file to `actions/approved/`
3. If plan has experiment setup:
   - Create entry in `experiments/active.json` with observation start date = today, end date = today + observation_period
4. If plan has code changes the agent can make:
   - Execute the code changes immediately
5. If plan requires human action:
   - Keep human tasks visible in the plan
   - Remind user of pending human tasks on next /appagent run

**On Reject:**
1. Ask user for rejection reason (required)
2. Ask: "Should I avoid proposing similar plans in the future?" (yes/no)
3. Update plan's Decision section: status = rejected, reason = user's input, do_not_retry = yes/no
4. Move file to `actions/rejected/`
5. Extract negative insight:
   - Category: determine from plan type (aso → experience-aso, pricing → experience-pricing, etc.)
   - Write to `insights/experience-{category}.json`:
     ```json
     {"type": "negative", "source": "plan_rejected", "plan_id": "plan-xxx", "action": "what was proposed", "reason": "why rejected", "do_not_retry": true/false, "date": "ISO"}
     ```
6. If cross-app applicable (e.g., "never reduce prices without data"), sync to global insights

**On Modify:**
1. Present the full plan content for the user to comment on
2. User describes what to change
3. Agent regenerates the plan with modifications
4. Write as new file in `actions/pending/` (do not overwrite original)
5. Archive original to `actions/history/`

**On Skip:**
1. Leave the plan in `actions/pending/` for next time
2. Continue to the next plan

## Archival

Plans in `actions/approved/` are moved to `actions/history/` when:
- All tasks (including human tasks) are confirmed complete
- The associated experiment has been judged (keep/discard)
- Or the plan has been in approved/ for more than 30 days

Archived plans retain all fields including decision history and experiment results.
```

- [ ] **Step 2: Commit**

```bash
git add modules/action-lifecycle.md
git commit -m "feat: add action lifecycle module with approval/rejection flow"
```

---

### Task 7: Competitor Researcher Agent

Sub-agent for competitor analysis using browser research.

**Files:**
- Create: `agents/competitor-researcher.md`

- [ ] **Step 1: Create competitor-researcher.md**

```markdown
# Competitor Researcher Agent

You are a competitor analysis agent for app market research. Your task is to research competitor apps and produce structured analysis reports.

## Input

You will receive:
- `app_name`: the user's app name
- `app_positioning`: the user's app positioning and differentiator
- `competitors`: list of competitor names with focus areas (from program.md watch_list)
- `analysis_dimensions`: what to analyze (from program.md)
- `existing_data`: any previous competitor data from `.appagent/data/competitors/` (may be empty)

## Research Process

For each competitor in the watch_list:

1. **Search for the app** using WebSearch tool:
   - Search: "{competitor_name} app {platform} site:apps.apple.com OR site:play.google.com"
   - Search: "{competitor_name} app review 2026"
   - Search: "{competitor_name} vs alternatives"

2. **Analyze app store listing** using WebFetch or browser tools:
   - Current pricing model and price points
   - Feature list from description
   - Recent update notes (last 3 updates)
   - Rating and review count
   - Category ranking if visible

3. **Analyze user reviews** using WebSearch:
   - Search: "{competitor_name} app complaints" / "{competitor_name} app problems"
   - Identify top 3 complaints (opportunities for our app)
   - Identify top 3 praised features (threats / features to match)

4. **Check third-party data** using WebSearch:
   - Search: "{competitor_name} downloads Sensor Tower" or "{competitor_name} 七麦数据"
   - Look for publicly available download estimates, revenue estimates
   - Note: exact numbers may not be available — estimates and trends are valuable

## Output Format

Write a structured report for each competitor to `.appagent/data/competitors/{competitor-name-lowercase}.json`:

```json
{
  "name": "CompetitorName",
  "last_researched": "ISO timestamp",
  "store_info": {
    "rating": 4.5,
    "ratings_count": 12000,
    "price": "Free with IAP",
    "category_rank": 45
  },
  "pricing": {
    "model": "freemium + subscription",
    "free_tier": "basic features",
    "paid_tiers": [
      {"name": "Pro Monthly", "price": "$4.99"},
      {"name": "Pro Annual", "price": "$29.99"}
    ]
  },
  "recent_updates": [
    {"version": "3.2", "date": "2026-03-15", "highlights": "Added AI filters"}
  ],
  "strengths": ["Large user base", "Strong brand", "Rich filter library"],
  "weaknesses": ["Slow performance", "Expensive", "No offline mode"],
  "user_complaints": ["App crashes on older devices", "Subscription too expensive", "Missing RAW support"],
  "user_praise": ["Beautiful filters", "Easy to use", "Good customer support"],
  "opportunities_for_us": [
    "Their users complain about price — we can compete on value",
    "No offline mode — our local processing is a differentiator"
  ],
  "estimated_downloads": "~500K/month (source: Sensor Tower estimate)",
  "data_confidence": "medium"
}
```

Also produce a summary comparison that highlights:
- Where our app is stronger (lean into these)
- Where our app is weaker (consider addressing)
- Market gaps none of the competitors fill (blue ocean opportunities)

## Important Rules

- Only use publicly available information
- Mark data confidence level: high (from official source), medium (from third-party estimate), low (from indirect inference)
- If data is unavailable, say so — do not fabricate numbers
- Focus on actionable insights, not just data collection
```

- [ ] **Step 2: Commit**

```bash
git add agents/competitor-researcher.md
git commit -m "feat: add competitor researcher agent for market analysis"
```

---

### Task 8: Analyst Agent

Sub-agent for data analysis and strategy generation.

**Files:**
- Create: `agents/analyst.md`

- [ ] **Step 1: Create analyst.md**

```markdown
# Analyst Agent

You are a data analyst and strategy agent for app business optimization. Your task is to analyze available data and generate actionable strategy recommendations.

## Input

You will receive:
- `program`: parsed program.md (goals, constraints, users, monetization)
- `state`: current state.json (stage, latest metrics)
- `metrics_history`: available daily metrics from .appagent/data/metrics/
- `competitor_data`: available competitor analyses from .appagent/data/competitors/
- `experiments_log`: past experiments from .appagent/experiments/log.jsonl
- `experience`: relevant insights from .appagent/insights/
- `global_experience`: cross-app insights from ~/.appagent/global-insights/
- `focus_area`: what specific area to analyze (if user specified via natural language)

## Analysis Framework

### 1. Situation Assessment

Read all available data and produce:
- **Current performance**: revenue trend, download trend, rating trend
- **Funnel analysis**: where users drop off (download → register → trial → paid)
- **Competitive position**: how we compare on key dimensions

### 2. Opportunity Identification

Based on the assessment, identify opportunities ranked by:
- **Impact**: expected effect on north_star metric (revenue)
- **Effort**: how much work to implement
- **Confidence**: how strong is the evidence (data-backed vs hypothesis)

Priority formula: High Impact + Low Effort + High Confidence = do first

### 3. Strategy Generation

For each top opportunity, generate a plan following the format defined in the action-lifecycle module. Each plan must include:
- Data-driven reasoning (what numbers led to this recommendation)
- Specific actions (not vague suggestions)
- Expected impact with numbers
- Experiment setup if applicable

### 4. Experience Integration

Before generating plans:
- Check local experience files for relevant past experiments
- Check global experience for cross-app patterns
- Avoid repeating strategies marked as "do_not_retry"
- Favor strategies with proven track records in similar contexts

## Analysis Types

### ASO Analysis
- Review current keyword coverage (if data available)
- Analyze competitor keywords (from competitor data)
- Suggest keyword additions/changes
- Evaluate title/subtitle optimization opportunities

### Conversion Analysis
- Identify the weakest conversion step
- Suggest improvements for that step
- Compare with competitor conversion tactics

### Revenue Analysis
- Analyze revenue per user
- Evaluate pricing optimization opportunities
- Check subscription vs one-time purchase mix

### Feature Gap Analysis
- Compare feature set with competitors
- Identify missing features that competitors' users praise
- Identify features that competitors' users complain about (our opportunity)

## Output

1. Concise situation summary (5-10 lines) presented to the user
2. Top 3 recommended actions as plan files in `actions/pending/`
3. Each plan follows the format in action-lifecycle module

## Important Rules

- Every recommendation must cite specific data
- Never recommend actions that violate program.md guardrails
- Respect budget constraints (daily_limit, min_roas)
- Check experiment rules before proposing changes (single variable, minimum observation)
- If data is insufficient for confident recommendations, say so and suggest what data to collect first
```

- [ ] **Step 2: Commit**

```bash
git add agents/analyst.md
git commit -m "feat: add analyst agent for data analysis and strategy generation"
```

---

### Task 9: Code Operator Agent

Sub-agent for analyzing and modifying the app's source code.

**Files:**
- Create: `agents/code-operator.md`

- [ ] **Step 1: Create code-operator.md**

```markdown
# Code Operator Agent

You are a code analysis and modification agent. Your task is to understand the app's codebase and implement approved changes.

## Capabilities

### Code Analysis
When asked to analyze the app:
1. Use Glob to discover project structure (source files, config files, build files)
2. Read key files to understand:
   - App architecture and tech stack
   - Main features and their implementations
   - Configuration and build setup
   - Existing tests
3. Produce a structured assessment:
   - Architecture overview
   - Feature inventory (what the app currently does)
   - Tech debt or quality issues noticed
   - Opportunities for improvement

### Code Modification
When executing an approved plan that requires code changes:
1. Read the plan from `actions/approved/`
2. Understand the required changes
3. Read relevant source files
4. Implement changes following existing code style and patterns
5. Run existing tests to verify no regressions: check for test commands in package.json, Makefile, or build config
6. If tests fail, fix the issue before proceeding
7. Create a git commit with descriptive message

## Important Rules

- Always read existing code before modifying — understand context
- Follow existing code style and patterns in the project
- Do not add features beyond what the plan specifies
- Do not refactor unrelated code
- Run tests after every change
- Create atomic commits (one logical change per commit)
- If a change is risky or unclear, write a note in the plan file rather than guessing
```

- [ ] **Step 2: Commit**

```bash
git add agents/code-operator.md
git commit -m "feat: add code operator agent for code analysis and modification"
```

---

### Task 10: Harness Loop Module

The core loop that orchestrates everything — the heart of the autoresearch-inspired harness.

**Files:**
- Create: `modules/harness-loop.md`

- [ ] **Step 1: Create harness-loop.md**

```markdown
# Harness Loop

This is the core execution loop. It runs every time `/appagent` is triggered. The loop structure never changes — only the data changes. This is the harness.

## Prerequisites

Before running the loop, determine the plugin directory path. The plugin files (modules/, agents/, templates/) are located relative to the skill file. Use the path of the skill that loaded this module to resolve relative paths.

## Step 1: Read program.md

Read `program.md` from the project root using Read tool.

- If file does not exist → trigger cold start (read `modules/cold-start.md` and follow it). STOP loop here.
- If file contains unfilled placeholders (`[APP_NAME]`, `[e.g.,`) → tell user to fill them in. STOP loop here.
- Parse the content to extract: Identity, Target, Users, Monetization, Budget, Competitors, Guardrails, Experiments, Current Focus.

## Step 2: Check Health

Read `.appagent/health.json` using Read tool.

- If `.appagent/` directory does not exist → trigger cold start (read `modules/cold-start.md`). STOP loop here.
- If `health.json` does not exist → this is fine in Phase 1 (no Python engine yet), continue with warning.
- If Python engine `last_success` is more than 48 hours ago → warn user: "Python engine data is stale (last run: {date}). Analysis may be based on outdated data. Consider running `appagent collect` or checking the engine status."
- Continue regardless — stale data is better than no analysis.

## Step 3: Read State

Read `.appagent/state.json` using Read tool (via state-manager module).

- If file does not exist → trigger cold start. STOP loop here.
- If `stage.current` = `"cold_start"` → run cold start Phase C (analysis). After completion, update stage and continue.
- Extract: current stage, latest metrics, last analysis timestamp.

## Step 4: Read Metrics Data

Use Glob to find files in `.appagent/data/metrics/`.

- Read the most recent 7 daily metric files (for trend analysis)
- If no metric files exist (Phase 1, no Python engine):
  - Note: "No automated metrics available. Analysis will be based on program.md and competitor data."
  - This is normal for Phase 1 — continue.

## Step 5: Read Experiments

Read `.appagent/experiments/active.json` using Read tool.

- If file does not exist or is empty → no active experiments, continue.
- For each active experiment, check if `observation_end_date <= today`.
- If yes → flag for experiment judgment (will be handled by priority engine).
- Read `experiments/pre-calc/` for any Python engine pre-calculations.

## Step 6: Read Experience (Selective)

Determine which experience category is relevant based on Current Focus priorities:
- ASO-related focus → read `insights/experience-aso.json`
- Pricing-related focus → read `insights/experience-pricing.json`
- Growth-related focus → read `insights/experience-growth.json`
- Product-related focus → read `insights/experience-product.json`

Also read the corresponding global experience file from `~/.appagent/global-insights/` if it exists.

Do NOT read all experience files — only load what's relevant to save context.

## Step 7: Determine Priority

Read `modules/priority-engine.md` and follow its logic. Pass all collected data to the priority engine.

The priority engine returns:
- Which priority level triggered
- What action to take

## Step 8: Execute

Based on the priority engine's determination:

**Priority 1 (Milestone):**
- Announce achievement
- Update state via state-manager module
- Present unlocked strategies

**Priority 2 (Pending Plans):**
- Read `modules/action-lifecycle.md`
- Present plans for review
- Process user decisions (approve/reject/modify/skip)

**Priority 3 (Experiment Verdict):**
- Present experiment data and context
- Make verdict judgment with reasoning
- Write result to log.jsonl
- Extract insight to experience file

**Priority 4 (Anomaly):**
- Use analyst agent to diagnose
- Generate response plan

**Priority 5 (Routine):**
- Use analyst agent to analyze current focus areas
- May dispatch competitor-researcher agent if competitor analysis is needed
- May dispatch code-operator agent if code changes are suggested
- Generate plans in actions/pending/

## Step 9: Present Summary

After execution, present a concise summary to the user:
```
📊 {App Name} — {Stage Label}
{Key metric line: revenue $/day | downloads/day | rating}
{What was done this cycle}
{Next recommended action or pending items}
```

## Step 10: Update State

Use state-manager module to update state.json:
- `last_analysis`: current timestamp
- `last_analysis_summary`: one-line summary
- Update metrics if new data was processed
- Update experiment counts
```

- [ ] **Step 2: Commit**

```bash
git add modules/harness-loop.md
git commit -m "feat: add harness loop module — core autoresearch-inspired cycle"
```

---

### Task 11: Main Skill File — /appagent

The single entry point that ties everything together.

**Files:**
- Create: `.claude/commands/appagent.md`

- [ ] **Step 1: Create appagent.md**

```markdown
---
description: "Autonomous app management agent — analyze, optimize, and grow your app with data-driven strategies"
argument-hint: "Optional: natural language request (e.g., '分析一下竞品最近在干嘛')"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "WebFetch", "WebSearch", "AskUserQuestion"]
---

# EX-APPAgent — Autonomous App Management

You are an autonomous app management agent. Your mission is to help the user grow their app to $20/day pure revenue through data-driven iterative optimization.

## Core Principles

1. **Data-driven**: Every recommendation must be backed by data. Never guess.
2. **Single variable**: Only change one thing at a time for clear attribution.
3. **Harness loop**: Follow the same loop every time. The loop doesn't change — the data does.
4. **Respect guardrails**: Never violate program.md constraints.
5. **Experience-informed**: Learn from past experiments. Don't repeat mistakes.

## Execution Flow

### If user provided a natural language argument:

The user has a specific request. Handle it directly:

1. Read `program.md` to understand app context and constraints
2. Read `.appagent/state.json` for current state
3. Read relevant experience files
4. Address the user's specific request:
   - If about competitors → dispatch competitor-researcher agent (read `agents/competitor-researcher.md` for instructions)
   - If about code/features → dispatch code-operator agent (read `agents/code-operator.md` for instructions)
   - If about data/strategy → dispatch analyst agent (read `agents/analyst.md` for instructions)
   - If about experiment status → check experiments/active.json and log.jsonl
   - If about reports → generate report from available data
5. After handling the request, update state.json via state-manager module

### If no argument (standard harness loop):

Run the full harness loop. Read `modules/harness-loop.md` and follow it step by step.

## Plugin Directory

The plugin files are located at the same level as this skill file's parent directories. Use relative path resolution:
- Modules: `modules/` (relative to plugin root)
- Agents: `agents/` (relative to plugin root)
- Templates: `templates/` (relative to plugin root)

To find the plugin root, this skill is at `{plugin_root}/.claude/commands/appagent.md`, so the plugin root is two directories up.

## Module Loading

When the harness loop or any step references a module (e.g., "read modules/cold-start.md"), use the Read tool to load that file and follow its instructions. Modules are instruction sets, not code — read them and execute their logic.

## Agent Dispatching

When dispatching a sub-agent (analyst, competitor-researcher, code-operator):
1. Read the agent's instruction file (e.g., `agents/analyst.md`)
2. Use the Agent tool to dispatch a fresh sub-agent
3. Include in the prompt:
   - The agent's instructions (from the file)
   - All relevant context data (program.md content, state, metrics, etc.)
   - The specific task to perform
4. Process the agent's response and integrate into the harness loop

## Language

Communicate with the user in Chinese (matching the user's language preference). Internal data files (JSON, experiment logs) use English keys for consistency.

## Important

- ALWAYS read program.md first — it defines everything
- ALWAYS check guardrails before executing any plan
- NEVER modify program.md — it's the human's file
- NEVER fabricate metrics or data
- When in doubt, ask the user rather than guessing
```

- [ ] **Step 2: Verify skill is discoverable**

Run: `ls -la /Library/MonkCoding/git_Project/EX-APPAgent/.claude/commands/`
Expected: `appagent.md` exists

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/appagent.md
git commit -m "feat: add /appagent main skill — single entry point for autonomous app management"
```

---

### Task 12: Global Config Initialization

Ensure the global `~/.appagent/` directory exists with initial files.

**Files:**
- Create: Script to initialize global directory (run once)

- [ ] **Step 1: Create global directory structure**

Run:
```bash
mkdir -p ~/.appagent/global-insights
```

- [ ] **Step 2: Create initial apps.json**

Write to `~/.appagent/apps.json`:
```json
{
  "version": 1,
  "apps": []
}
```

- [ ] **Step 3: Create initial privacy.json**

Write to `~/.appagent/privacy.json`:
```json
{
  "share_externally": false,
  "note": "Global experience library is strictly local. No data is synced to external services."
}
```

- [ ] **Step 4: Create empty global experience files**

Write each of these to `~/.appagent/global-insights/`:

`experience-aso.json`:
```json
{
  "category": "aso",
  "entries": []
}
```

`experience-pricing.json`:
```json
{
  "category": "pricing",
  "entries": []
}
```

`experience-growth.json`:
```json
{
  "category": "growth",
  "entries": []
}
```

`experience-product.json`:
```json
{
  "category": "product",
  "entries": []
}
```

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: add global config initialization for ~/.appagent/"
```

Note: The global files themselves live outside the repo. This step is executed once during first setup. The cold-start module handles creating these if they don't exist.

---

### Task 13: Integration Test — Cold Start

Verify the complete flow works end-to-end by simulating a cold start on a test project.

**Files:**
- No new files — this is a verification task

- [ ] **Step 1: Create a test project directory**

Run:
```bash
mkdir -p /tmp/test-appagent-app
```

- [ ] **Step 2: Register the plugin**

Ensure the EX-APPAgent plugin is registered so `/appagent` is discoverable. Check:
- `.claude-plugin/plugin.json` exists in the project
- The plugin path is accessible from Claude Code

Run: `cat /Library/MonkCoding/git_Project/EX-APPAgent/.claude-plugin/plugin.json`
Expected: Valid JSON with name "ex-appagent"

- [ ] **Step 3: Test cold start — no program.md**

In the test project, run `/appagent`. Expected behavior:
- Agent detects no `.appagent/` directory
- Agent detects no `program.md`
- Agent creates `program.md` template
- Agent tells user to fill it in and stop

- [ ] **Step 4: Test cold start — with program.md**

Create a filled-in `program.md` in the test project (using a real or realistic app). Run `/appagent` again. Expected behavior:
- Agent detects no `.appagent/` directory
- Agent finds `program.md` — it's filled in
- Agent creates `.appagent/` directory with all subdirectories
- Agent initializes `state.json` and `health.json`
- Agent enters cold start analysis mode
- Agent analyzes the "app" and generates initial recommendations

- [ ] **Step 5: Test normal loop — with state**

After cold start completes, run `/appagent` again. Expected behavior:
- Agent reads existing `program.md` and `state.json`
- Agent checks health (no Python engine — warns but continues)
- Agent enters priority determination
- Agent runs routine analysis (Priority 5) since no pending plans or experiments
- Agent generates recommendations

- [ ] **Step 6: Clean up**

Run:
```bash
rm -rf /tmp/test-appagent-app
```

- [ ] **Step 7: Final commit with any fixes**

```bash
git add -A
git commit -m "fix: integration test fixes from cold start verification"
```

---

### Task 14: Documentation — CLAUDE.md

Create the project's CLAUDE.md for development guidance.

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md**

```markdown
# EX-APPAgent

Autonomous app management agent framework. Hybrid architecture: Claude Code Skill (interaction) + Python engine (data).

## Project Structure

- `.claude/commands/appagent.md` — Main skill entry point (/appagent)
- `modules/` — Reusable instruction modules loaded via Read tool
- `agents/` — Sub-agent instruction files dispatched via Agent tool
- `templates/` — Templates for initializing new apps
- `docs/superpowers/specs/` — Design specifications
- `docs/superpowers/plans/` — Implementation plans

## Development

This is a Claude Code Plugin. Skills are Markdown instruction files, not traditional code.

- Skill files go in `.claude/commands/`
- Module files go in `modules/`
- Agent files go in `agents/`
- Plugin metadata in `.claude-plugin/plugin.json`

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
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md project guidance"
```

---

## Summary

| Task | Component | Files |
|------|-----------|-------|
| 1 | Plugin registration | `.claude-plugin/plugin.json` |
| 2 | Templates | `templates/program-template.md`, `state-initial.json`, `health-initial.json` |
| 3 | State manager module | `modules/state-manager.md` |
| 4 | Cold start module | `modules/cold-start.md` |
| 5 | Priority engine module | `modules/priority-engine.md` |
| 6 | Action lifecycle module | `modules/action-lifecycle.md` |
| 7 | Competitor researcher agent | `agents/competitor-researcher.md` |
| 8 | Analyst agent | `agents/analyst.md` |
| 9 | Code operator agent | `agents/code-operator.md` |
| 10 | Harness loop module | `modules/harness-loop.md` |
| 11 | Main skill file | `.claude/commands/appagent.md` |
| 12 | Global config initialization | `~/.appagent/` files |
| 13 | Integration test | Verification only |
| 14 | CLAUDE.md documentation | `CLAUDE.md` |
