# Capability Expansion Workflow

When the agent identifies a capability gap during analysis, follow this workflow to propose, validate, and activate a new extension.

## When to Trigger

This module is triggered when during routine analysis (Priority 5), the agent realizes:
- "I need to analyze review sentiment but can only count star ratings"
- "I need to detect keyword cannibalization but don't have that logic"
- "I need to parse competitor pricing tiers from store pages"

## Step 1: Generate Expansion Request

Create a plan file in `actions/pending/` with type `capability_expansion`:

```markdown
# Plan: Capability Expansion — {Name}

**ID:** plan-{YYYY-MM-DD}-ext-{short-name}
**Created:** {ISO timestamp}
**Type:** capability_expansion
**Priority:** medium

## Need
{What capability is missing and why it matters}

## Reason
{What analysis task was blocked or limited without this capability}

## Proposed Implementation

**File:** `engine/src/appagent_engine/extensions/{name}.py`

### Code

```python
{Complete code for the extension. Must have a run(input_data: dict) -> dict function.}
```

### Safety Check Results

Run via Bash: `python3 -c "
from appagent_engine.guardrails import validate_extension_code
code = open('path_to_temp_file').read()
result = validate_extension_code(code)
print(result)
"`

Display results:
- File access: {✅ or ✗ with details}
- Network: {✅ or ✗ with details}
- Sensitive paths: {✅ or ✗ with details}
- Dangerous imports: {✅ or ✗ with details}

## Decision
- Status: pending
```

**Important:** The code must be complete and functional. No placeholders or TODOs.

## Step 2: User Review

Present the plan to the user as part of Priority 2 (Pending Plans) on the next run.

The user can:
- **Approve** → proceed to Step 3
- **Reject** → record reason, do not implement
- **Modify** → user suggests changes, agent regenerates

## Step 3: Write Extension Code

After approval:

1. Write the code to `engine/src/appagent_engine/extensions/{name}.py` using Write tool
2. Verify the file was created: `ls engine/src/appagent_engine/extensions/{name}.py`

## Step 4: Dry Run

Run the extension in sandbox mode to verify it works:

```bash
cd engine && uv run python3 -c "
from appagent_engine.extensions.loader import dry_run_extension
result = dry_run_extension('{name}', {mock_input_json})
print(result)
"
```

Present the dry-run output to the user:
- If `success: true` → show output, ask "Activate this extension?"
- If `success: false` → show error, ask if they want to fix it or discard

## Step 5: Activate

If dry-run passes and user confirms:

```bash
cd engine && uv run python3 -c "
from appagent_engine.extensions.loader import activate_extension
activate_extension('{name}', '{description}')
print('✓ Extension activated')
"
```

Move the plan from `actions/pending/` to `actions/approved/`.

The extension is now available for future analysis cycles. The agent can call it via:
```python
from appagent_engine.extensions.loader import load_extension
ext = load_extension('{name}')
result = ext.run(input_data)
```

## Safety Constraints

Extensions MUST:
- Only write to `.appagent/` directories
- Only access whitelisted network domains
- Not access sensitive paths (~/.ssh, ~/.aws, etc.)
- Not use subprocess, shutil, or ctypes
- Have a `run(input_data: dict) -> dict` entry point
- Be pure Python (no C extensions or binary dependencies)

If any safety check fails, the extension MUST NOT be written to disk.
