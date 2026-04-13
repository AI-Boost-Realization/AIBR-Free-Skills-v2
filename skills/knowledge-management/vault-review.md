---
name: vault-review
description: Periodic vault review — daily note creation, weekly summary, monthly retrospective with archival suggestions
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
user_invocable: true
argument-hint: "[daily|weekly|monthly]"
---

# Vault Review

Periodic review skill for a markdown knowledge vault. Works with any PARA-structured vault at `~/.vault/`.

## Auto-Detect Review Type

If no argument given:
- Before noon → daily
- Sunday → weekly
- 1st of month → monthly
- Otherwise → daily

---

## Daily Review

### 1. Create daily note
- Check if `~/.vault/05-Daily/{YYYY}/{MM}/{YYYY-MM-DD}.md` exists
- If not, create from Daily template
- Replace `{{date:...}}` placeholders with actual values

### 2. Populate from context
- Check git log for today's commits across known repos:
  ```bash
  for repo in ~/Code/project-a ~/Code/project-b ~/Code/project-c; do
    cd "$repo" 2>/dev/null && git log --oneline --since="today" 2>/dev/null
  done
  ```
- Check Claude memory for any new files created today
- Fill in Work Log sections with findings

### 3. Surface priorities
- Read the most recent weekly review for "Next Week Priorities"
- Echo them as today's focus items

### Output
```
Daily note: {filepath}
Commits found: {count}
Priorities: {list from weekly}
```

---

## Weekly Review

### 1. Create weekly note
- Path: `~/.vault/05-Daily/Weekly/{YYYY}-W{WW}.md`
- Use Weekly template

### 2. Auto-populate
- List all daily notes from this week
- List all decision/learning notes created this week (grep frontmatter `created:` dates)
- List active projects from `01-Projects/` with status

### 3. Prompt user
Ask: "Any blockers or priorities for next week?"
Add response to the weekly note.

### Output
```
Weekly review: {filepath}
Days logged: {count}/7
Decisions this week: {count}
Learnings this week: {count}
```

---

## Monthly Review

### 1. Create monthly note
- Path: `~/.vault/05-Daily/Monthly/{YYYY}-{MM}.md`

### 2. Auto-populate
- Summarize all weekly reviews from this month
- List all decisions made (from frontmatter queries)
- Count notes created per domain
- Count tasks completed

### 3. Archive check
- Scan `01-Projects/` for any project with no activity in 30+ days
- Suggest archival to `04-Archive/`

### 4. Vault hygiene
- Check for notes in `00-Inbox/` older than 7 days (need triage)
- Check for notes with missing frontmatter
- Report findings

### Output
```
Monthly review: {filepath}
Notes created this month: {count}
Decisions: {count}
Inbox items needing triage: {count}
Projects suggested for archive: {list}
```
