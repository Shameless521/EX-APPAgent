# Harness Loop

This is the core execution loop. It runs every time `/appagent` is triggered. The loop structure never changes — only the data changes. This is the harness.

## Prerequisites

Before running the loop, determine the plugin directory path. The plugin files (modules/, agents/, templates/) are located relative to the skill file. Use the path of the skill that loaded this module to resolve relative paths.

## Step 1: Read program.md

Read `program.md` from the project root using Read tool.

- If file does not exist → trigger cold start (read `modules/cold-start.md` and follow it). STOP loop here.
- If file contains unfilled placeholders (`[APP_NAME]`, `[e.g.,`) → tell user to fill them in. STOP loop here.
- Parse the content to extract: Identity, Target, Users, Monetization, Budget, Competitors, Guardrails, Experiments, Current Focus.

## Step 2: Check Health & Engine

Read `.appagent/health.json` using Read tool.

- If `.appagent/` directory does not exist → trigger cold start (read `modules/cold-start.md`). STOP loop here.
- If `health.json` has `python_engine.status` = `"not_configured"` or `"not_installed"`:
  - Check if engine is installed: `which appagent 2>/dev/null`
  - If not installed → offer to install: "Data engine not found. Want me to install it? This enables automated metrics collection."
  - If user agrees → run `uv tool install "appagent-engine @ git+https://github.com/Shameless521/EX-APPAgent#subdirectory=engine"` and then `appagent collect`
  - If user declines → continue in Phase 1 mode (LLM-only analysis)
- If `health.json` does not exist → continue with warning (Phase 1 mode is fine).
- Extract: `data_freshness` timestamps, `api_status`, last run time.

## Step 3: Read State

Read `.appagent/state.json` using Read tool (via state-manager module).

- If file does not exist → trigger cold start. STOP loop here.
- If `stage.current` = `"cold_start"` → run cold start Phase C (analysis). After completion, update stage and continue.
- Extract: current stage, latest metrics, last analysis timestamp, active experiments.

## Step 3.5: Smart Collection Decision

**This is where the agent decides what data to refresh — no hardcoded rules.**

Read the following to inform the decision:
1. `health.json` → `data_freshness` (when each category was last collected)
2. `state.json` → current stage, `last_analysis_summary` (any anomalies or follow-ups?)
3. `experiments/active.json` → what metrics are being observed?
4. `insights/experience-ops.json` → past collection decisions and their outcomes
5. User's input → did they ask about something specific?

**Make a collection decision by reasoning through:**

```
I need to decide what data to collect. Let me consider:

1. USER INTENT: Did the user ask about something specific?
   - "看看收入" → only need metrics
   - "竞品怎么样" → only need competitors
   - No specific request → proceed to other factors

2. ACTIVE EXPERIMENTS: What's being observed right now?
   - ASO experiment running → ASO rankings are critical
   - Pricing experiment → metrics (revenue) are critical
   - No experiments → no special priority

3. DATA GAPS: What dates are missing in metrics/?
   - Last metric file is 2026-04-12, today can get up to 2026-04-13
   → Need to backfill 2026-04-13

4. FRESHNESS: When was each category last collected?
   - metrics: 2026-04-13 (yesterday) → fresh enough unless experiment needs it
   - aso: 2026-04-13 (yesterday) → check if experiment cares
   - competitors: 2026-04-08 (7 days ago) → getting stale
   - reviews: 2026-04-13 → fine

5. FOLLOW-UP: Did last analysis flag anything?
   - "Revenue anomaly detected" → must refresh metrics + competitors
   - "New app version released" → must refresh reviews
   - Nothing unusual → routine check

6. OPS EXPERIENCE: What did I learn from past collection decisions?
   - Read experience-ops.json for patterns like:
     "pricing_experiment → always collect [metrics, reviews]"
     "revenue anomaly → always collect [metrics, competitors]"

DECISION: collect [categories], backfill [dates], reason: "..."
```

**Execute the decision:**

If collection is needed, run via Bash:
```bash
appagent collect --app "<app_name>" --only <categories> --dates <dates_or_backfill>
```

If no collection needed, note: "Data is fresh, proceeding with analysis."

**If collection fails**: Do NOT block. Continue analysis with existing data, note the failure.

## Step 4: Read Metrics Data

Use Glob to find files in `.appagent/data/metrics/`.

- Read the most recent 7 daily metric files (for trend analysis)
- If no metric files exist:
  - Note: "No metrics data available. Analysis will be based on program.md and competitor data."
  - Continue — qualitative analysis is still valuable.

## Step 5: Read Experiments

Read `.appagent/experiments/active.json` using Read tool.

- If file does not exist or is empty → no active experiments, continue.
- For each active experiment, check if `observation_end_date <= today`.
- If yes → flag for experiment judgment (will be handled by priority engine).
- Read `experiments/pre-calc/` for any Python engine pre-calculations.

## Step 6: Read Experience (Selective)

Determine which experience categories are relevant based on Current Focus priorities and the current analysis context:
- ASO-related focus → read `insights/experience-aso.json`
- Pricing-related focus → read `insights/experience-pricing.json`
- Growth-related focus → read `insights/experience-growth.json`
- Product-related focus → read `insights/experience-product.json`
- Always read `insights/experience-ops.json` (operational experience, used in Step 3.5 and 9.5)

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

## Step 9.5: Reflect on Collection & Record Ops Experience

**After the analysis is complete, reflect on the data quality and collection decision.**

Think through:

```
REFLECTION on this analysis cycle:

1. DATA UTILIZATION: Which collected data did I actually use in the analysis?
   - Used: metrics (for revenue trend), aso (for keyword experiment)
   - Not used: competitors (collected but irrelevant to today's priority)

2. DATA GAPS: Was there a moment I wished I had data I didn't collect?
   - "Wanted to check if review sentiment changed after the update, but didn't collect reviews"
   - "Needed competitor pricing data but it was 10 days stale"

3. PATTERNS OBSERVED: Any data behavior worth remembering?
   - "Revenue stable Mon-Fri, dips on weekends"
   - "ASO rankings fluctuated more than usual — might be seasonal"

4. COLLECTION EFFICIENCY: Was this cycle's collection decision good?
   - ✓ Good: collected exactly what was needed
   - ✗ Over-collected: fetched competitors but didn't use them
   - ✗ Under-collected: should have fetched reviews
```

**Record the reflection** by writing to `.appagent/insights/experience-ops.json`:

Use Bash to run a Python one-liner or use Write tool to append a JSON entry:

```json
{
  "date": "<today>",
  "context": "<stage + active experiments + user intent>",
  "collected": ["<categories actually collected>"],
  "used_in_analysis": ["<categories that informed the output>"],
  "missed": ["<categories I wished I had>"],
  "pattern": "<any reusable rule discovered, or null>",
  "lesson": "<one-sentence takeaway for future decisions>"
}
```

Only write an ops experience entry if there's something genuinely worth learning:
- **DO record**: "During pricing experiments, reviews matter" (new pattern)
- **DO record**: "Competitor data was stale and caused a wrong assumption" (mistake to avoid)
- **DON'T record**: "Everything was fine, data was fresh" (no learning value)

**Cross-app sync**: If the pattern is universal (not app-specific), also write to `~/.appagent/global-insights/experience-ops.json`.

## Step 10: Update State

Use state-manager module to update state.json:
- `last_analysis`: current timestamp
- `last_analysis_summary`: one-line summary
- Update metrics if new data was processed
- Update experiment counts
