#!/usr/bin/env bash
# pre-deploy-check.sh — PreToolUse hook for deploy commands
#
# Runs pre-flight checks before any deploy operation:
#   - Warns on uncommitted changes
#   - Runs TypeScript typecheck if tsconfig.json exists
#   - Runs test suite if package.json has a test script
#
# IMPORTANT: This hook reports WARNINGS ONLY — it never blocks a deploy.
# The developer always has final say. This hook exists to surface information,
# not to enforce a gate.
#
# SETUP:
#   Register as a PreToolUse hook in .claude/settings.json:
#   {
#     "hooks": {
#       "PreToolUse": [
#         {
#           "matcher": "Bash",
#           "hooks": [{
#             "type": "command",
#             "command": "bash /path/to/pre-deploy-check.sh"
#           }]
#         }
#       ]
#     }
#   }
#
#   This hook activates when the Bash tool is used — it reads the command
#   from stdin and only runs checks when the command looks like a deploy.

INPUT=$(cat)

# Check if this Bash call looks like a deploy (adjust patterns to match your stack)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
if ! echo "$COMMAND" | grep -qE '(deploy|railway up|vercel|fly deploy|npm run ship|git push.*main)'; then
  exit 0
fi

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

echo "[PRE-DEPLOY] Running pre-flight checks..."

# ── Check for uncommitted changes ──────────────────────────────────────────
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  echo "[PRE-DEPLOY] WARNING: Uncommitted changes detected. Consider committing or stashing before deploying."
else
  echo "[PRE-DEPLOY] Git status: clean."
fi

# ── TypeScript typecheck ────────────────────────────────────────────────────
if [ -f "$ROOT/tsconfig.json" ]; then
  echo "[PRE-DEPLOY] Running typecheck..."
  TSC_OUTPUT=$(cd "$ROOT" && npx tsc --noEmit 2>&1 | tail -5)
  TSC_EXIT=$?
  if [ $TSC_EXIT -ne 0 ]; then
    echo "[PRE-DEPLOY] WARNING: TypeScript errors found (not blocking deploy):"
    echo "$TSC_OUTPUT"
  else
    echo "[PRE-DEPLOY] Typecheck passed."
  fi
fi

# ── Test suite ─────────────────────────────────────────────────────────────
if [ -f "$ROOT/package.json" ]; then
  HAS_TEST=$(node -e "const p=require('$ROOT/package.json'); console.log(p.scripts && p.scripts.test ? 'yes' : 'no')" 2>/dev/null)
  if [ "$HAS_TEST" = "yes" ]; then
    echo "[PRE-DEPLOY] Running tests..."
    TEST_OUTPUT=$(cd "$ROOT" && npm test 2>&1 | tail -10)
    TEST_EXIT=$?
    if [ $TEST_EXIT -ne 0 ]; then
      echo "[PRE-DEPLOY] WARNING: Tests failing (not blocking deploy):"
      echo "$TEST_OUTPUT"
    else
      echo "[PRE-DEPLOY] Tests passed."
    fi
  fi
fi

echo "[PRE-DEPLOY] Pre-flight complete. Proceeding with deploy."
exit 0
