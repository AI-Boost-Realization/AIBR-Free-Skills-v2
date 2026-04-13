---
name: vault-inbox
description: GTD-style inbox processing — triage unsorted notes in 00-Inbox, add frontmatter, route to correct PARA folder
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
user_invocable: true
---

# Vault Inbox

Process all notes in `~/.vault/00-Inbox/` using GTD triage: classify, add frontmatter, route to the correct PARA folder.

## Step 1: List inbox contents

```bash
ls ~/.vault/00-Inbox/*.md 2>/dev/null
```

If empty: output "Inbox is clean." and stop.

## Step 2: Process each file

For each `.md` file in inbox:

### 2a. Read content
Read the file. Determine:
- **Domain**: which project/area does this relate to? (project-a, project-b, personal, work)
- **Type**: what kind of note is this? (decision, learning, bug, idea, reference, meeting)
- **Status**: active, done, review

### 2b. Add/fix frontmatter
If frontmatter is missing or incomplete, add it:
```yaml
---
domain: {determined}
type: {determined}
status: active
created: {file creation date or today}
updated: {today}
tags: [{domain}, type/{type}]
---
```

### 2c. Determine destination

| Type | Destination |
|------|-------------|
| Active project work | `01-Projects/{project}/` |
| Decision | `01-Projects/{project}/` or `02-Areas/{domain}/` |
| Learning/bug | `03-Resources/Engineering/` or `03-Resources/{topic}/` |
| Reference | `03-Resources/{topic}/` |
| Meeting note | `02-Areas/{domain}/` or `01-Projects/{project}/` |
| Idea (not actionable yet) | Keep in `00-Inbox/` with `#status/review` tag |
| Completed/old | `04-Archive/` |

### 2d. Move file
```bash
mv ~/.vault/00-Inbox/{filename} ~/.vault/{destination}/
```

### 2e. Add cross-links
Search vault for related notes, add `## Related` links section.

### 2f. Update MOC
If a Map of Content exists for the domain, add a link to the new note.

## Step 3: Report

```
═══ INBOX PROCESSED ─────────────────────────
  Total: {count} items
  Routed:
  • {filename} → {destination} ({domain}/{type})
  • {filename} → {destination} ({domain}/{type})
  Kept in inbox: {count} (need human review)
═══════════════════════════════════════════════
```
