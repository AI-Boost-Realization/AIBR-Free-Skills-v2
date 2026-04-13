#!/usr/bin/env bash
# vault-structure-audit.sh — SessionStart hook
#
# Full PARA structure audit: detects non-canonical dirs, daily path issues,
# cross-directory duplicate filenames, and missing frontmatter (sampled).
# Rate-limited to once per 24h. Writes report to shared-state/.
# Emits additionalContext only when issues are found (silent on clean vault).
#
# SETUP:
#   Set VAULT to your markdown vault directory.
#   Register as a SessionStart hook in .claude/settings.json.

VAULT="${CLAUDE_VAULT_PATH:-$HOME/.vault}"
REPORT="$HOME/.claude/shared-state/vault-structure-report.md"
LAST_RUN="$HOME/.claude/shared-state/.vault-structure-audit-last-run"
RATE_LIMIT_SECONDS=86400  # 24 hours

# Only run if vault exists
if [ ! -d "$VAULT" ]; then
    exit 0
fi

# Rate limit check
if [ -f "$LAST_RUN" ]; then
    LAST_RUN_TIME=$(stat -f %m "$LAST_RUN" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    ELAPSED=$(( NOW - LAST_RUN_TIME ))
    if [ "$ELAPSED" -lt "$RATE_LIMIT_SECONDS" ]; then
        exit 0
    fi
fi

mkdir -p "$(dirname "$REPORT")"

python3 << PYEOF
import re, random
from pathlib import Path
from datetime import datetime

VAULT = Path("${VAULT}").expanduser()
REPORT = Path("${REPORT}").expanduser()

# Directories to skip during analysis
EXCLUDE_DIRS = {
    '.git', '.trash', '.obsidian', '.smart-env', '.claude',
}

# Canonical PARA top-level directories
# Customize this set if your vault uses different top-level names
PARA_TOP_LEVEL = {
    '00-central', '00-Inbox', '01-Projects', '02-Areas',
    '03-Resources', '04-Archive', '05-Daily', '06-Templates',
    '07-Attachments', '08-Canvas', '09-MOCs'
}

# Infrastructure/index files that are expected to be duplicated by name
INFRA_FILES = {
    'CLAUDE.md', 'MEMORY.md', 'README.md', 'Home.md',
    'PROJECTS.md', 'INFRASTRUCTURE.md'
}

issues = []

def is_excluded(path):
    rel = str(path.relative_to(VAULT))
    return any(ex in rel for ex in EXCLUDE_DIRS)


# ── 1. Non-canonical top-level directories ─────────────────────────────────
non_para_dirs = []
for d in VAULT.iterdir():
    if not d.is_dir():
        continue
    if d.name.startswith('.'):
        continue
    if d.name not in PARA_TOP_LEVEL:
        non_para_dirs.append(d.name)

if non_para_dirs:
    issues.append(f"Non-PARA top-level dirs ({len(non_para_dirs)}): {', '.join(sorted(non_para_dirs))}")


# ── 2. Daily note path anomalies ───────────────────────────────────────────
daily_root = VAULT / '05-Daily'
path_anomalies = []
if daily_root.exists():
    for year_dir in daily_root.iterdir():
        if not year_dir.is_dir(): continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir(): continue
            # Flag non-numeric month dirs (e.g. "01-January" instead of "01")
            if re.match(r'^\d{2}-.+', month_dir.name):
                path_anomalies.append(str(month_dir.relative_to(VAULT)))

if path_anomalies:
    issues.append(f"Non-canonical daily month dirs ({len(path_anomalies)}): {', '.join(path_anomalies)}")


# ── 3. Duplicate filename scan ─────────────────────────────────────────────
filename_to_paths = {}
for f in VAULT.rglob('*.md'):
    if is_excluded(f): continue
    if f.name in INFRA_FILES: continue
    if f.name not in filename_to_paths:
        filename_to_paths[f.name] = []
    filename_to_paths[f.name].append(str(f.relative_to(VAULT)))

duplicates = {k: v for k, v in filename_to_paths.items() if len(v) > 1}
if duplicates:
    dup_list = [f"{k}: [{', '.join(v)}]" for k, v in list(duplicates.items())[:10]]
    issues.append(
        f"Duplicate filenames ({len(duplicates)}): " + "; ".join(dup_list[:3]) +
        (f" ... +{len(dup_list)-3} more" if len(dup_list) > 3 else "")
    )


# ── 4. Missing frontmatter sample ──────────────────────────────────────────
all_md = [f for f in VAULT.rglob('*.md')
          if not is_excluded(f) and f.name not in INFRA_FILES]
sample = random.sample(all_md, min(20, len(all_md)))
missing_fm = []
for f in sample:
    try:
        text = f.read_text()[:400]
        if not re.search(r'^domain:', text, re.MULTILINE):
            missing_fm.append(f.name)
    except Exception:
        pass

if missing_fm:
    issues.append(f"Missing frontmatter in sample ({len(missing_fm)}/20): {', '.join(missing_fm[:5])}")


# ── Write report ────────────────────────────────────────────────────────────
now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
lines = [f"# Vault Structure Audit — {now}\n"]

if not issues:
    lines.append("**Status: CLEAN — no structural issues detected.**\n")
    lines.append(f"- Vault: {len(all_md)} notes scanned\n")
    lines.append(f"- PARA top-level dirs: all canonical\n")
    lines.append(f"- Daily note paths: all canonical\n")
    lines.append(f"- Duplicate filenames: none\n")
    lines.append(f"- Frontmatter sample (20): all present\n")
else:
    lines.append(f"**Status: {len(issues)} issue(s) detected**\n\n")
    for issue in issues:
        lines.append(f"- {issue}\n")

REPORT.write_text(''.join(lines))

# ── Output additionalContext if issues found ────────────────────────────────
if issues:
    import json
    n_dup = len(duplicates)
    n_para = len(non_para_dirs)
    n_split = len(path_anomalies)
    summary = (f"[vault-audit] {len(issues)} issue(s): {n_dup} duplicates, "
               f"{n_para} non-PARA dirs, {n_split} path anomalies — "
               f"see ~/.claude/shared-state/vault-structure-report.md")
    print(json.dumps({"additionalContext": summary}))
# Clean vault — silent exit

PYEOF

# Update rate-limit timestamp
touch "$LAST_RUN"
