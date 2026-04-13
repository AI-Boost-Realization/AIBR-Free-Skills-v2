# Knowledge Management Suite

A 4-skill system for building and maintaining a persistent, AI-assisted knowledge base using the PARA method (Projects, Areas, Resources, Archive). Designed to integrate with Obsidian but works with any markdown-based note system.

## The Problem

Claude Code sessions are ephemeral. Insights, decisions, and hard-won debugging knowledge disappear when the session ends. These skills create a durable layer that persists across sessions, surfaces relevant context automatically, and keeps your vault organized over time.

## The Skills

### vault-capture
Write any insight, decision, or learning to the vault with proper metadata and routing. Invoke it mid-session when something is worth preserving.

```
/vault-capture "Redis cache TTL should match session length" --type decision --domain my-app
```

### vault-sync
Automatically bridge Claude Code's auto-memory files (the `memory/` directories inside `.claude/projects/`) into the vault. Converts Claude memory frontmatter format to Obsidian-compatible YAML and routes by file-naming convention.

```
/vault-sync
```

### vault-review
Periodic review cycles: daily notes, weekly summaries, monthly retrospectives. Auto-populates from git log and existing vault content. Flags projects for archival and surfaces inbox items that need triage.

```
/vault-review daily
/vault-review weekly
/vault-review monthly
```

### vault-inbox
GTD-style processing for `00-Inbox/`. Reads each file, classifies it, adds missing frontmatter, and moves it to the correct PARA folder. Keeps a running report of what was routed where.

```
/vault-inbox
```

## PARA Structure

```
~/.vault/
  00-Inbox/          # Unprocessed captures
  01-Projects/       # Active projects with a defined outcome
  02-Areas/          # Ongoing responsibilities (no end date)
  03-Resources/      # Reference material by topic
  04-Archive/        # Completed or inactive items
  05-Daily/          # Daily, weekly, monthly notes
  06-Templates/      # Note templates
  09-MOCs/           # Maps of Content (domain indexes)
```

## How It All Connects

```
Claude session insight
        ↓
  /vault-capture  ──→  vault note with frontmatter + cross-links
        ↓
  session-end hook ──→ queues new auto-memory files
        ↓
  next /session-start ──→ vault-sync-auto.sh drains queue
        ↓
  /vault-inbox ──→ processes any unrouted inbox items
        ↓
  /vault-review ──→ weekly: surfaces priorities + decisions made
```

## Setup

1. Create your vault directory: `mkdir -p ~/.vault/{00-Inbox,01-Projects,02-Areas,03-Resources,04-Archive,05-Daily,06-Templates,09-MOCs}`
2. Add the skills to your `.claude/skills/` directory
3. Optionally add `vault-sync-auto.sh` as a SessionStart hook for automatic syncing

## Customization

The PARA routing in `vault-sync` and `vault-capture` uses filename prefixes (`feedback_`, `project_`, `reference_`, `user_`) and domain keywords to determine destination. Edit the routing tables in each skill to match your own domain/project names.
