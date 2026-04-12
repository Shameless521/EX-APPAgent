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
