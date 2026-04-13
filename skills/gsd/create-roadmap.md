---
name: gsd:create-roadmap
description: Create roadmap with phases for the project
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
  - Glob
---

<objective>
Create project roadmap with phase breakdown.

Roadmaps define what work happens in what order. Run after /gsd:new-project.
</objective>

<context>
@.planning/PROJECT.md
@.planning/config.json
</context>

<process>

<step name="validate">
```bash
# Verify project exists
[ -f .planning/PROJECT.md ] || { echo "ERROR: No PROJECT.md found. Run /gsd:new-project first."; exit 1; }
```
</step>

<step name="check_existing">
Check if roadmap already exists:

```bash
[ -f .planning/ROADMAP.md ] && echo "ROADMAP_EXISTS" || echo "NO_ROADMAP"
```

**If ROADMAP_EXISTS:**
Use AskUserQuestion:
- header: "Roadmap exists"
- question: "A roadmap already exists. What would you like to do?"
- options:
  - "View existing" - Show current roadmap
  - "Replace" - Create new roadmap (will overwrite)
  - "Cancel" - Keep existing roadmap

If "View existing": `cat .planning/ROADMAP.md` and exit
If "Cancel": Exit
If "Replace": Continue with workflow
</step>

<step name="create_roadmap">
Analyze the project brief and create a phase breakdown:

- Detect the domain and project type from PROJECT.md
- Identify logical phases with clear goals and dependencies
- Flag phases that need research (niche domains, specialized libraries)
- Confirm phases with user (respecting config.json mode setting)
- Create ROADMAP.md with full phase structure
- Initialize STATE.md for progress tracking
- Create phase directories under .planning/phases/
- Commit the roadmap
</step>

<step name="done">
```
Roadmap created:
- Roadmap: .planning/ROADMAP.md
- State: .planning/STATE.md
- [N] phases defined

---

## Next Up

**Phase 1: [Name]** — [Goal from ROADMAP.md]

`/gsd:plan-phase 1`

(`/clear` first for a fresh context window)

---

**Also available:**
- `/gsd:discuss-phase 1` — gather context first
- `/gsd:research-phase 1` — investigate unknowns
- Review roadmap

---
```
</step>

</process>

<output>
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/XX-name/` directories
</output>

<success_criteria>
- [ ] PROJECT.md validated
- [ ] ROADMAP.md created with phases
- [ ] STATE.md initialized
- [ ] Phase directories created
- [ ] Changes committed
</success_criteria>
