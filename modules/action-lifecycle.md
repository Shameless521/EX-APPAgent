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
