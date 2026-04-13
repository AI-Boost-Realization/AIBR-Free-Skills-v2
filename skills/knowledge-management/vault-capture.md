---
name: vault-capture
description: Write a durable learning, decision, or idea to a markdown vault with proper frontmatter, PARA routing, and cross-links
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep"]
user_invocable: true
argument-hint: "[title] --domain [project-a|project-b|personal] --type [decision|learning|bug|idea|reference]"
---

# Vault Capture

Write a note to your markdown knowledge vault with proper PARA routing, frontmatter, and cross-links. Compatible with Obsidian and any markdown-based knowledge system.

## Step 1: Parse Input

Extract from arguments or infer from context:
- **title**: descriptive name (e.g., "API Rate Limit Retry Strategy Decision")
- **domain**: which project or area this belongs to (e.g., my-app, personal, work)
- **type**: decision, learning, bug, idea, reference, meeting

If not provided, infer from the current conversation context.

## Step 2: Choose Template + Route

| Type | Template | Destination |
|------|----------|-------------|
| decision | Decision template | `01-Projects/{project}/` or `02-Areas/{domain}/` |
| learning, bug | Learning template | `03-Resources/Engineering/` (tech) or domain folder |
| idea | none (freeform) | `00-Inbox/` |
| reference | none (freeform) | `03-Resources/{subtopic}/` |
| meeting | none (freeform) | `01-Projects/{project}/` or `02-Areas/{domain}/` |

## Step 3: Generate Note

Create the file with this structure:

```markdown
---
domain: {domain}
type: {type}
status: active
project: {project if applicable}
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
tags: [{domain}, type/{type}]
---
# {title}

{content — fill from conversation context or user input}
```

Use the template structure if one matches:
- **Decision**: Context / Decision / Consequences / Alternatives
- **Learning**: Problem / Root Cause / Fix / Prevention

## Step 4: Add Cross-Links

Search the vault for related notes:
```
Grep for keywords from the title in ~/.vault/ --glob "*.md"
```

Add a `## Related` section at the bottom with `[note title](path/to/note.md)` links to any related notes found.

## Step 5: Update MOC

If a Map of Content (MOC) exists for this domain at `~/.vault/09-MOCs/{Domain} MOC.md`:
- Read it
- Add a link to the new note under the appropriate section
- If no appropriate section, add under a new `## Recent` section

## Step 6: Confirm

Output:
```
Captured to vault: {filepath}
Domain: {domain} | Type: {type}
Related notes linked: {count}
MOC updated: {yes/no}
```
