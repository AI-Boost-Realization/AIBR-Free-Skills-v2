---
name: vault-sync
description: Bridge Claude Code auto-memory files into a markdown vault with proper frontmatter and PARA routing
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
user_invocable: true
---

# Vault Sync

Bridges Claude Code auto-memory files (`~/.claude/projects/*/memory/`) into your markdown knowledge vault (`~/.vault/`).

## When to Run
- After session start (check sync queue)
- Manually via `/vault-sync`
- Triggered by session-end hook (queues for next session)

## Workflow

### Step 1: Find new/updated memory files

Scan all project memory directories:
```bash
find ~/.claude/projects/*/memory/ -name "*.md" -not -name "MEMORY.md" -newer ~/.vault/.last-vault-sync 2>/dev/null
```

If `.last-vault-sync` doesn't exist, use files modified in the last 7 days:
```bash
find ~/.claude/projects/*/memory/ -name "*.md" -not -name "MEMORY.md" -mtime -7 2>/dev/null
```

### Step 2: For each memory file

1. **Read the file** — extract YAML frontmatter (name, description, type)
2. **Check for duplicates** — grep the vault for the `name:` value
3. **Route by type**:

| Memory Type | Vault Destination |
|-------------|-------------------|
| `project` | `01-Projects/{domain}/` or `02-Areas/{domain}/` |
| `feedback` | `03-Resources/Engineering/` (if tech) or `02-Areas/` (if workflow) |
| `reference` | `03-Resources/{topic}/` |
| `user` | `02-Areas/Personal/` |

4. **Transform frontmatter** — convert Claude memory format to vault format:

Claude memory format:
```yaml
---
name: Some Memory Title
description: one-line description
type: project
---
```

Vault (Obsidian-compatible) format:
```yaml
---
domain: {inferred from path or content}
type: {mapped from memory type}
status: active
created: {file mtime}
updated: {file mtime}
tags: [{domain}, type/{type}]
source: claude-memory
---
```

5. **Add cross-links** — search vault for related notes, add `## Related` section
6. **Write the note** to the destination

### Step 3: Update sync timestamp
```bash
touch ~/.vault/.last-vault-sync
```

### Step 4: Report

```
═══ VAULT SYNC ─────────────────────────────
  Scanned: {count} memory directories
  New notes: {count} synced to vault
  Updated: {count} existing notes refreshed
  Skipped: {count} (already in vault)

  Synced:
  • {filename} → {vault path}
  • {filename} → {vault path}
═══════════════════════════════════════════════
```

## Edge Cases
- If a memory file has no frontmatter: route to `00-Inbox/` for manual triage
- If domain can't be inferred: check the project directory name (e.g., `-Users-[username]-Code-myapp-backend` → domain: myapp)
- Never overwrite vault files — if a note exists at the destination, append changes or skip
