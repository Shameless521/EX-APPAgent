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
- If `health.json` has `python_engine.status` = `"not_configured"` or `"not_installed"`:
  - Check if engine is installed: `which appagent 2>/dev/null`
  - If not installed → offer to install: "Data engine not found. Want me to install it? This enables automated metrics collection."
  - If user agrees → run `uv tool install "appagent-engine @ git+https://github.com/Shameless521/EX-APPAgent#subdirectory=engine"` and then `appagent collect`
  - If user declines → continue in Phase 1 mode (LLM-only analysis)
- If `health.json` does not exist → continue with warning (Phase 1 mode is fine).
- If Python engine `last_success` is more than 48 hours ago → warn user: "Data is stale (last collected: {date}). Running a quick refresh..." and execute `appagent collect` in the background.
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
