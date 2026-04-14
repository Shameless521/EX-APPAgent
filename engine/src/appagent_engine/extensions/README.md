# Extensions

Agent-written capability extensions. All extensions must comply with these constraints:

## Rules

1. **File access**: Only write to `.appagent/` directories and `engine/extensions/`
2. **Network**: Only access whitelisted domains (see `guardrails.py`)
3. **Sensitive paths**: Never access `~/.ssh`, `~/.aws`, `~/.gnupg`, etc.
4. **Validation**: All writes go through `guardrails.validate_file_path()`
5. **Dry-run first**: New extensions must run in dry-run mode before activation

## Adding an Extension

1. Agent generates code + full diff in `actions/pending/`
2. Safety checks run automatically
3. User reviews and approves
4. Code is placed in this directory
5. Dry-run mode executes with mock output
6. If dry-run passes, extension is activated
