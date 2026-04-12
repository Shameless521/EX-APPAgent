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
