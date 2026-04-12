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
