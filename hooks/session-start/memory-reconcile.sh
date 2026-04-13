#!/usr/bin/env bash
# memory-reconcile.sh — SessionStart hook (rate-limited: once per 24h)
#
# 1. Walks MEMORY.md links — flags dead ones (file doesn't exist in vault)
# 2. Scans vault/**/*.md — flags orphans (no MEMORY.md entry)
# 3. Writes report to shared-state/memory-drift.md
# 4. Emits additionalContext only if drift is found
#
# SETUP:
#   Set MEMORY_INDEX to your MEMORY.md path.
#   Set VAULT to your markdown vault directory.
#   Register as a SessionStart hook in .claude/settings.json.

RATE_FILE="$HOME/.claude/shared-state/.memory-reconcile-last-run"
REPORT="$HOME/.claude/shared-state/memory-drift.md"
MEMORY_INDEX="${CLAUDE_MEMORY_INDEX:-$HOME/.claude/projects/$(whoami)/memory/MEMORY.md}"
VAULT="${CLAUDE_VAULT_PATH:-$HOME/.vault}"

mkdir -p "$HOME/.claude/shared-state"

# Rate limit: only run once per 24 hours
if [ -f "$RATE_FILE" ]; then
  LAST=$(cat "$RATE_FILE")
  NOW=$(date +%s)
  AGE=$((NOW - LAST))
  [ "$AGE" -lt 86400 ] && exit 0
fi

python3 - <<PYEOF
import os, re, json
from pathlib import Path
from datetime import datetime, timezone

index_path = Path("${MEMORY_INDEX}").expanduser()
vault_path = Path("${VAULT}").expanduser()
report_path = Path.home() / ".claude/shared-state/memory-drift.md"
rate_file = Path.home() / ".claude/shared-state/.memory-reconcile-last-run"

dead_links = []
indexed_files = set()

if index_path.exists():
    content = index_path.read_text()
    # Extract markdown links: [text](path) or [text](./path) or [text](../../path)
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', content):
        link_path_raw = m.group(2)
        # Skip external URLs
        if link_path_raw.startswith("http"):
            continue
        # Resolve relative to index file's parent
        resolved = (index_path.parent / link_path_raw).resolve()
        indexed_files.add(str(resolved))
        if not resolved.exists():
            dead_links.append(f"  DEAD LINK: {link_path_raw}")

# Find vault files not in the index
orphans = []
if vault_path.exists():
    for md_file in sorted(vault_path.rglob("*.md")):
        str_path = str(md_file.resolve())
        # Skip infra files and templates
        if md_file.name in ("CLAUDE.md", "MEMORY.md", "README.md") or "06-Templates" in str_path:
            continue
        if str_path not in indexed_files:
            rel = md_file.relative_to(vault_path)
            orphans.append(f"  ORPHAN (not indexed): {rel}")

ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
drift_exists = dead_links or orphans

if drift_exists:
    lines = [f"# Memory Drift Report — {ts}", ""]
    if dead_links:
        lines.append(f"## Dead MEMORY.md links ({len(dead_links)})")
        lines.extend(dead_links[:40])
        lines.append("")
    if orphans:
        lines.append(f"## Vault files with no MEMORY.md entry ({len(orphans)})")
        lines.extend(orphans[:40])
        if len(orphans) > 40:
            lines.append(f"  ... and {len(orphans)-40} more")
        lines.append("")
    report_path.write_text("\n".join(lines))

    summary = (f"MEMORY DRIFT: {len(dead_links)} dead link(s), {len(orphans)} orphan vault file(s). "
               f"See ~/.claude/shared-state/memory-drift.md")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary
        }
    }
    import sys, json
    print(json.dumps(output))

# Update rate limit timestamp
import time
rate_file.write_text(str(int(time.time())))
PYEOF
