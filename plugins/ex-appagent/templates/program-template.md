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
