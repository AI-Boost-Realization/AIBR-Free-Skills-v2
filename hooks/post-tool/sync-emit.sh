#!/bin/bash
# sync-emit.sh — Cross-session event emitter
#
# Writes structured events to a shared append-only JSONL event log.
# Use this to track tool usage, memory writes, and deploys across
# multiple Claude Code sessions working on the same project.
#
# USAGE (called directly):
#   bash sync-emit.sh <event_type> '<json_payload>'
#   bash sync-emit.sh memory.write '{"path": "~/.vault/01-Projects/foo.md"}'
#   bash sync-emit.sh deploy.started '{"env": "production", "service": "api"}'
#
# USAGE (as PostToolUse hook):
#   Called by Claude Code with hook context on stdin — auto-extracts fields.
#
# Always exits 0 — sync failures must never block Claude's work.

EVENT_TYPE="${1:-unknown}"
PAYLOAD="${2:-}"

EVENT_LOG="${CLAUDE_EVENT_LOG:-$HOME/.claude/shared-state/event-log.jsonl}"

# Read hook context from stdin if available
STDIN_JSON=""
if [ ! -t 0 ]; then
  STDIN_JSON=$(cat)
fi

if [ -n "$STDIN_JSON" ]; then
  SESSION_ID=$(echo "$STDIN_JSON" | jq -r '.session_id // empty' 2>/dev/null)
  AGENT_ID=$(echo "$STDIN_JSON" | jq -r '.agent_id // .subagent_type // "main"' 2>/dev/null)
  TASK_TITLE=$(echo "$STDIN_JSON" | jq -r '.task.title // empty' 2>/dev/null)
  CWD=$(echo "$STDIN_JSON" | jq -r '.cwd // empty' 2>/dev/null)
  # Derive event type from hook event name if not explicitly provided
  if [ -z "$EVENT_TYPE" ] || [ "$EVENT_TYPE" = "unknown" ]; then
    EVENT_TYPE=$(echo "$STDIN_JSON" | jq -r '.hook_event_name // "unknown"' 2>/dev/null)
  fi
  # Build payload from hook context if not explicitly provided
  if [ -z "$PAYLOAD" ]; then
    PAYLOAD=$(echo "$STDIN_JSON" | jq -c '{tool_name: .tool_name, tool_input: .tool_input, agent_id: .agent_id, task: .task}' 2>/dev/null || echo '{}')
  fi
else
  SESSION_ID=""
  AGENT_ID="main"
  TASK_TITLE=""
  CWD=""
fi

# Fallbacks
[ -z "$SESSION_ID" ] && SESSION_ID="term-${PPID}"
[ -z "$AGENT_ID" ]   && AGENT_ID="main"
[ -z "$PAYLOAD" ]    && PAYLOAD="{}"

# Derive project from cwd
if [ -n "$CWD" ]; then
  PROJECT=$(basename "$CWD")
else
  PROJECT="unknown"
fi
[ -z "$PROJECT" ] && PROJECT="unknown"

# Ensure event log directory exists
mkdir -p "$(dirname "$EVENT_LOG")"
touch "$EVENT_LOG" 2>/dev/null || exit 0

# Get next sequence number
SEQ=$(wc -l < "$EVENT_LOG" 2>/dev/null | tr -d ' ')
SEQ=$((SEQ + 1))

# ISO 8601 timestamp (UTC)
TS=$(date -u "+%Y-%m-%dT%H:%M:%SZ")

# Validate payload is JSON; fall back to empty object
if ! echo "$PAYLOAD" | jq empty 2>/dev/null; then
  PAYLOAD="{}"
fi

# Memory conflict detection: if this is a memory.write event, check for
# another session writing to the same path within the last 30 minutes.
if [ "$EVENT_TYPE" = "memory.write" ]; then
  WRITE_PATH=$(echo "$PAYLOAD" | jq -r '.path // ""' 2>/dev/null)
  if [ -n "$WRITE_PATH" ]; then
    THIRTY_MINS_AGO=$(date -u -v-30M "+%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)
    if [ -n "$THIRTY_MINS_AGO" ]; then
      CONFLICT_SID=$(tail -100 "$EVENT_LOG" 2>/dev/null | \
        jq -r --arg path "$WRITE_PATH" \
               --arg sid "$SESSION_ID" \
               --arg cutoff "$THIRTY_MINS_AGO" \
          'select(.type == "memory.write" and .sid != $sid and (.payload.path // "") == $path and .ts >= $cutoff) | .sid' \
          2>/dev/null | tail -1)
      if [ -n "$CONFLICT_SID" ]; then
        PAYLOAD=$(echo "$PAYLOAD" | jq --arg csid "$CONFLICT_SID" '. + {conflict_with: $csid}' 2>/dev/null || echo "$PAYLOAD")
      fi
    fi
  fi
fi

# Build the JSONL event line
EVENT=$(jq -cn \
  --argjson seq "$SEQ" \
  --arg ts "$TS" \
  --arg sid "$SESSION_ID" \
  --arg project "$PROJECT" \
  --arg type "$EVENT_TYPE" \
  --argjson payload "$PAYLOAD" \
  '{seq: $seq, ts: $ts, sid: $sid, project: $project, type: $type, payload: $payload}' \
  2>/dev/null)

[ -z "$EVENT" ] && exit 0

# Atomic append: use flock if available (Linux), otherwise plain append (macOS)
if command -v flock >/dev/null 2>&1; then
  (
    flock -x 9
    echo "$EVENT" >> "$EVENT_LOG"
  ) 9>"${EVENT_LOG}.lock"
else
  echo "$EVENT" >> "$EVENT_LOG"
fi

# Rotate log if it exceeds 500KB
LOG_SIZE=$(wc -c < "$EVENT_LOG" 2>/dev/null | tr -d ' ')
if [ "$LOG_SIZE" -gt 512000 ]; then
  mv "$EVENT_LOG" "${EVENT_LOG}.$(date +%Y%m%d-%H%M%S).bak"
  touch "$EVENT_LOG"
fi

exit 0
