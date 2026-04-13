#!/usr/bin/env bash
# post-edit-typecheck.sh — PostToolUse hook on Write|Edit
#
# When a TypeScript file is edited, finds the nearest tsconfig.json and runs
# tsc --noEmit. Injects additionalContext with errors if typecheck fails.
# Silently no-ops for non-TS files or projects without tsconfig.json.
#
# SETUP:
#   Register as a PostToolUse hook in .claude/settings.json:
#   {
#     "hooks": {
#       "PostToolUse": [
#         { "matcher": "Write|Edit", "hooks": [{ "type": "command", "command": "bash /path/to/post-edit-typecheck.sh" }] }
#       ]
#     }
#   }

set -e

python3 - <<'PYEOF'
import json, os, sys, subprocess
from pathlib import Path

try:
    raw = sys.stdin.read()
    data = json.loads(raw) if raw.strip() else {}
except Exception:
    data = {}

# Extract edited file path from hook payload
file_path = (
    data.get("tool_input", {}).get("file_path")
    or data.get("tool_input", {}).get("filePath")
    or data.get("tool_response", {}).get("filePath")
    or ""
)

if not file_path:
    sys.exit(0)

# Only run for TypeScript files
if not file_path.endswith((".ts", ".tsx")):
    sys.exit(0)

file_path = os.path.expanduser(file_path)
if not os.path.isfile(file_path):
    sys.exit(0)

# Find nearest tsconfig.json (walk up from the edited file)
search_dir = Path(file_path).parent
tsconfig = None
for parent in [search_dir] + list(search_dir.parents):
    candidate = parent / "tsconfig.json"
    if candidate.exists():
        tsconfig = candidate
        break
    # Stop at home dir or filesystem root to avoid runaway search
    if str(parent) in (os.path.expanduser("~"), "/"):
        break

if not tsconfig:
    sys.exit(0)

project_dir = str(tsconfig.parent)

# Find tsc: prefer local node_modules, fallback to global
tsc_candidates = [
    os.path.join(project_dir, "node_modules", ".bin", "tsc"),
    os.path.join(project_dir, "node_modules", "typescript", "bin", "tsc"),
]
tsc_cmd = None
for c in tsc_candidates:
    if os.path.isfile(c):
        tsc_cmd = c
        break
if not tsc_cmd:
    result = subprocess.run(["which", "tsc"], capture_output=True, text=True)
    if result.returncode == 0:
        tsc_cmd = result.stdout.strip()

if not tsc_cmd:
    sys.exit(0)  # No tsc available — skip silently

# Run typecheck
try:
    result = subprocess.run(
        [tsc_cmd, "--noEmit", "--pretty", "false"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=60
    )
except subprocess.TimeoutExpired:
    sys.exit(0)

if result.returncode == 0:
    sys.exit(0)  # Clean — no output needed

# Type errors found — inject as context so Claude fixes them immediately
errors = (result.stdout + result.stderr).strip()
lines = errors.splitlines()
if len(lines) > 30:
    lines = lines[:30] + [f"... and {len(lines)-30} more lines"]
errors_truncated = "\n".join(lines)

context = (
    f"TYPECHECK FAILED after editing {os.path.basename(file_path)}:\n"
    f"{errors_truncated}\n\n"
    f"Fix these before declaring work done."
)

output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": context
    }
}
print(json.dumps(output))
PYEOF
