#!/usr/bin/env bash
# vault-sync-auto.sh — Mechanical vault sync on SessionStart
# Finds new memory files in project dirs, routes to PARA, drains queue.
# No LLM needed — pure file routing by naming convention.
#
# SETUP:
#   Set VAULT to your markdown vault path.
#   Set INDEX to your MEMORY.md index path.
#   Register as a SessionStart hook in .claude/settings.json.

VAULT="${CLAUDE_VAULT_PATH:-$HOME/.vault}"
QUEUE="$VAULT/.vault-sync-queue"
LAST_SYNC="$VAULT/.last-vault-sync"
INDEX="${CLAUDE_MEMORY_INDEX:-$HOME/.claude/projects/$(whoami)/memory/MEMORY.md}"

# ── Find new files ─────────────────────────────────────────────────────────────
if [ -f "$LAST_SYNC" ]; then
    FIND_ARGS=(-newer "$LAST_SYNC")
else
    FIND_ARGS=(-mtime -7)
fi

NEW_FILES=$(find ~/.claude/projects/*/memory/ -name "*.md" -not -name "MEMORY.md" "${FIND_ARGS[@]}" 2>/dev/null)

if [ -z "$NEW_FILES" ]; then
    # Still drain queue even if no new files
    : > "$QUEUE" 2>/dev/null
    echo "[vault-sync] No new memory files. Queue drained."
    exit 0
fi

python3 << PYEOF
import re, shutil
from pathlib import Path
from datetime import datetime

VAULT = Path("${VAULT}").expanduser()
EXCLUDE = {'.git', '.trash', '.obsidian', '.smart-env', '.claude'}

# Canonical PARA top-level directories — anything outside this list is a drift signal
PARA_TOP_LEVEL = {
    '00-central', '00-Inbox', '01-Projects', '02-Areas',
    '03-Resources', '04-Archive', '05-Daily', '06-Templates',
    '07-Attachments', '08-Canvas', '09-MOCs'
}

# Active projects under 01-Projects/ — unknown domains go to 00-Inbox
# Customize this set to match your own project names
KNOWN_PROJECTS = {'ProjectA', 'ProjectB', 'PersonalWork', 'ClientWork'}

new_files_raw = """$NEW_FILES"""
new_files = [Path(f.strip()) for f in new_files_raw.strip().splitlines() if f.strip()]

# Build vault filename lookup for dedup check
vault_files = set()
for f in VAULT.rglob('*.md'):
    rel = str(f.relative_to(VAULT))
    if any(e in rel for e in EXCLUDE):
        continue
    vault_files.add(f.name)

def infer_domain(project_dir_name):
    """Map project directory name to domain label.
    Customize these mappings to match your own project directory names."""
    name = project_dir_name.lower()
    # Add your own project → domain mappings here:
    # if 'myapp' in name: return 'myapp'
    # if 'client-x' in name: return 'client-x'
    return 'personal'

# Map domain labels to vault Area subdirectories
# Customize to match your own PARA structure
DOMAIN_TO_AREA = {
    'personal': 'Personal',
    'work': 'Work',
    # Add your own:
    # 'myapp': 'MyApp',
    # 'client-x': 'ClientX',
}

# Keywords that route feedback/reference files to specific Resource subdirs
FEEDBACK_RESOURCE_KEYWORDS = {
    'Engineering': ['railway', 'docker', 'deploy', 'vercel', 'ci', 'typecheck',
                    'api', 'git', 'typescript', 'python', 'database', 'cache'],
    'DevOps': ['devops', 'infra', 'config', 'cron', 'trigger', 'webhook'],
    'AI-ML': ['llm', 'ai-', 'ml-', 'model', 'prompt', 'claude', 'openai'],
}

def route_to_para(filename, domain):
    """Return vault destination directory based on filename prefix and domain."""
    name = filename.lower()
    if name.startswith('feedback_'):
        for resource_dir, keywords in FEEDBACK_RESOURCE_KEYWORDS.items():
            if any(kw in name for kw in keywords):
                return VAULT / f'03-Resources/{resource_dir}'
        area = DOMAIN_TO_AREA.get(domain, 'Personal')
        return VAULT / f'02-Areas/{area}'
    elif name.startswith('project_'):
        domain_cap = domain.capitalize()
        if domain_cap in KNOWN_PROJECTS:
            dest = VAULT / f'01-Projects/{domain_cap}'
        else:
            print(f'[vault-sync] WARNING: unknown domain "{domain}" for {filename} — routing to 00-Inbox')
            return VAULT / '00-Inbox'
        if not dest.exists():
            dest = VAULT / '00-Inbox'
            print(f'[vault-sync] WARNING: 01-Projects/{domain_cap} does not exist — routing {filename} to 00-Inbox')
        return dest
    elif name.startswith('reference_'):
        for resource_dir, keywords in FEEDBACK_RESOURCE_KEYWORDS.items():
            if any(kw in name for kw in keywords):
                return VAULT / f'03-Resources/{resource_dir}'
        return VAULT / '03-Resources/General'
    elif name.startswith('user_'):
        area = DOMAIN_TO_AREA.get(domain, 'Personal')
        return VAULT / f'02-Areas/{area}'
    elif name.startswith('decision_'):
        domain_cap = domain.capitalize()
        if domain_cap in KNOWN_PROJECTS:
            return VAULT / f'01-Projects/{domain_cap}'
        return VAULT / '00-Inbox'
    elif name.startswith('learning_'):
        return VAULT / '03-Resources/Engineering'
    elif name.startswith('moc_'):
        return VAULT / '09-MOCs'
    else:
        return VAULT / '00-Inbox'


def validate_para_dest(dest_dir):
    """Verify destination is inside a canonical PARA top-level dir."""
    try:
        rel = dest_dir.relative_to(VAULT)
        top = str(rel).split('/')[0]
        if top not in PARA_TOP_LEVEL:
            print(f'[vault-sync] WARNING: non-PARA destination "{top}" — redirecting to 00-Inbox')
            return VAULT / '00-Inbox'
    except ValueError:
        print(f'[vault-sync] WARNING: destination {dest_dir} is outside vault — redirecting to 00-Inbox')
        return VAULT / '00-Inbox'
    return dest_dir


def add_vault_frontmatter(content, filename, domain, dest_dir):
    """Transform Claude memory frontmatter to vault-compatible (Obsidian) format."""
    fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not fm_match:
        # No frontmatter — add minimal
        mtime = datetime.now().strftime('%Y-%m-%d')
        new_fm = (f'---\ndomain: {domain}\ntype: reference\n'
                  f'tags: [{domain}, type/reference]\ncreated: {mtime}\n'
                  f'status: active\nsource: claude-memory\n---\n')
        return new_fm + content

    fm_text = fm_match.group(1)
    fields = {}
    for line in fm_text.splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            fields[k.strip()] = v.strip()

    fm_type = fields.get('type', 'reference')
    type_map = {'project': 'project', 'feedback': 'feedback',
                'reference': 'reference', 'user': 'user', 'note': 'feedback'}
    obs_type = type_map.get(fm_type, fm_type)
    obs_domain = fields.get('domain', domain)
    created = fields.get('created', datetime.now().strftime('%Y-%m-%d'))
    updated = fields.get('updated', created)
    tags_raw = fields.get('tags', f'[{obs_domain}, type/{obs_type}]')

    new_fm = (f'---\ndomain: {obs_domain}\ntype: {obs_type}\nstatus: active\n'
              f'created: {created}\nupdated: {updated}\ntags: {tags_raw}\n'
              f'source: claude-memory\n---\n')
    rest = content[fm_match.end():]
    return new_fm + rest

synced = 0
skipped = 0

for src in new_files:
    if not src.exists():
        continue

    filename = src.name
    if filename in vault_files:
        skipped += 1
        continue

    try:
        proj_dir = src.parent.parent.name  # projects/{proj-dir}/memory/file.md
        domain = infer_domain(proj_dir)
    except Exception:
        domain = 'personal'

    dest_dir = route_to_para(filename, domain)
    dest_dir = validate_para_dest(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    if dest_path.exists():
        skipped += 1
        continue

    try:
        content = src.read_text()
        transformed = add_vault_frontmatter(content, filename, domain, dest_dir)
        dest_path.write_text(transformed)
        synced += 1
    except Exception as e:
        print(f'[vault-sync] ERROR: {filename}: {e}')

print(f'[vault-sync] Synced: {synced}, Skipped (already exists): {skipped}')
PYEOF

# ── Update timestamp and drain queue ──────────────────────────────────────────
touch "$LAST_SYNC"
: > "$QUEUE" 2>/dev/null
