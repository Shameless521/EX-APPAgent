# Cold Start Protocol

## Detection

Cold start is detected when ANY of these are true:
- `.appagent/` directory does not exist
- `.appagent/state.json` does not exist
- `state.json` has `stage.current` = `"cold_start"`

---

## Phase 0: Ensure Python Engine is Ready

Before anything else, check if the data engine is available and configured.

### Step 0.1: Check Engine Installation

Run via Bash: `which appagent 2>/dev/null || uv tool list 2>/dev/null | grep appagent`

- If found → engine is installed, go to Step 0.2
- If NOT found → install it:
  1. Tell the user: "First time setup — installing the data engine..."
  2. Run: `uv tool install "appagent-engine @ git+https://github.com/Shameless521/EX-APPAgent#subdirectory=engine"`
  3. If `uv` is not available, try: `pip install "appagent-engine @ git+https://github.com/Shameless521/EX-APPAgent#subdirectory=engine"`
  4. If install fails → tell the user to install manually and continue without engine (Phase 1 mode)

### Step 0.2: Check Global Config

Run via Bash: `cat ~/.appagent/config.json 2>/dev/null`

- If file exists and has `appstore_connect.key_id` → config is ready, go to Phase A
- If file does NOT exist or is incomplete → run **Interactive Config Setup** below

### Interactive Config Setup

Guide the user through API key configuration in the conversation:

**App Store Connect** (ask the user):
1. "Do you have an App Store Connect API Key? (If not, go to App Store Connect → Users and Access → Integrations → App Store Connect API → Generate)"
2. If yes, ask for:
   - Key ID (from the key filename, e.g., AuthKey_XXXXXXXX.p8 → the XXXXXXXX part)
   - Issuer ID (UUID shown at the top of the API keys page)
   - Key file path (ask them to put the .p8 file in `~/.appagent/credentials/` and tell you the filename)
   - Vendor Number (from Payments and Financial Reports page)
3. If they don't have it or want to skip → set `appstore_connect` to null

**Google Play** (ask the user):
1. "Do you have a Google Play Developer account with a Service Account?"
2. If yes, ask for the JSON key file path (suggest `~/.appagent/credentials/google-play-service-account.json`)
3. If not → briefly explain how to create one, or skip

**Generate config:**

Create `~/.appagent/credentials/` directory if needed, then write `~/.appagent/config.json`:

```json
{
  "appstore_connect": {
    "key_id": "<from user>",
    "issuer_id": "<from user>",
    "private_key_path": "~/.appagent/credentials/<filename>.p8",
    "vendor_number": "<from user>"
  },
  "google_play": {
    "service_account_path": "~/.appagent/credentials/google-play-service-account.json"
  },
  "collection": {
    "metrics_time": "06:00",
    "reviews_interval_hours": 8
  }
}
```

Set any unconfigured platform to `null`. Partial config is fine — the engine gracefully skips unavailable platforms.

---

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

### Step B.1: Create directory structure

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

### Step B.2: Copy templates

- Read `templates/state-initial.json` → write to `.appagent/state.json`
- Read `templates/health-initial.json` → write to `.appagent/health.json`

### Step B.3: Auto-detect app info and register

Instead of asking the user for bundle IDs, **auto-detect from project files**:

**Detect project type** (check which files exist):
- `pubspec.yaml` → Flutter project
- `package.json` → React Native / web project
- `*.xcodeproj` → native iOS
- `build.gradle` → native Android

**For Flutter projects** (most common for this tool):

1. Read `pubspec.yaml` → extract `name` field as app name
2. Read `android/app/build.gradle` or `android/app/build.gradle.kts`:
   - Search for `applicationId` → this is the Android package name
   - Pattern: `applicationId "com.example.app"` or `applicationId = "com.example.app"`
3. Read `ios/Runner.xcodeproj/project.pbxproj`:
   - Search for `PRODUCT_BUNDLE_IDENTIFIER` → this is the iOS bundle ID
   - Pattern: `PRODUCT_BUNDLE_IDENTIFIER = com.example.app;`
   - Note: iOS and Android IDs may differ (e.g., `com.tto321.hairmakeover321` vs `com.tto.hairmakeover`)

**Register the app:**

Read `~/.appagent/apps.json` (create with `{"version": 1, "apps": []}` if not exists).

Check if an app with the same project path is already registered. If not, append:

```json
{
  "name": "<from pubspec.yaml or program.md>",
  "path": "<current project absolute path>",
  "registered_at": "<ISO timestamp>",
  "platforms": {
    "ios": {
      "bundle_id": "<auto-detected from project.pbxproj>",
      "store_url": "<from program.md store_url if available, else null>"
    },
    "android": {
      "package_name": "<auto-detected from build.gradle>",
      "store_url": "<from program.md store_url if available, else null>"
    }
  },
  "aso_keywords": []
}
```

Tell the user: "Auto-detected app: {name} (iOS: {bundle_id}, Android: {package_name}). Registered in global config."

If auto-detection fails for any platform, tell the user and ask them to provide the ID manually.

### Step B.4: Add .appagent/ to .gitignore

Check if `.gitignore` exists and contains `.appagent/`. If not, append it.

### Step B.5: Run first data collection

If the engine is installed and config exists:

1. Tell the user: "Running first data collection..."
2. Run via Bash: `appagent collect --app "<app_name>"`
3. If successful → metrics are now available for Phase C analysis
4. If failed → continue without metrics (Phase 1 mode), show the error

## Phase C: Cold Start Analysis

Since there's no historical data, the harness loop enters cold start mode:

1. **Analyze source code**: Read key source files to understand what the app does, its current features, tech stack
2. **Read global experience**: Load `~/.appagent/global-insights/` files if they exist (cross-app experience from other apps)
3. **Read collected data**: If Step B.5 succeeded, read the metrics and ASO data just collected
4. **Competitor research**: Use the competitor-researcher agent to analyze competitors from program.md watch_list via browser
5. **Generate initial strategy**: Based on code analysis + global experience + competitor research + fresh data, generate:
   - Initial assessment of the app's strengths and weaknesses
   - Top 3 recommended first actions
   - Suggested first experiment
   - If ASO data available: keyword ranking insights
6. Write recommendations to `actions/pending/` as plan files
7. Update `state.json`: set `stage.current` to first milestone stage (e.g., `"from_0_to_1"`)

Tell the user: "Cold start complete. I've analyzed your app and generated initial recommendations. Here's what I found: [summary]. Review the pending plans and let me know which to proceed with."
