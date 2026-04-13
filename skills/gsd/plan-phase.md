---
name: gsd:plan-phase
description: Create detailed execution plan for a phase (PLAN.md)
argument-hint: "[phase]"
allowed-tools:
  - Read
  - Bash
  - Write
  - Glob
  - Grep
  - AskUserQuestion
  - WebFetch
---

<objective>
Create executable phase prompt with discovery, context injection, and task breakdown.

Purpose: Break down roadmap phases into concrete, executable PLAN.md files that Claude can execute.
Output: One or more PLAN.md files in the phase directory (.planning/phases/XX-name/{phase}-{plan}-PLAN.md)
</objective>

<context>
Phase number: $ARGUMENTS (optional - auto-detects next unplanned phase if not provided)

**Load project state first:**
@.planning/STATE.md

**Load roadmap:**
@.planning/ROADMAP.md

**Load phase context if exists (created by /gsd:discuss-phase):**
Check for and read `.planning/phases/XX-name/{phase}-CONTEXT.md` - contains research findings, clarifications, and decisions from phase discussion.

**Load codebase context if exists:**
Check for `.planning/codebase/` and load relevant documents based on phase type.
</context>

<process>
1. Check .planning/ directory exists (error if not - user should run /gsd:new-project)
2. If phase number provided via $ARGUMENTS, validate it exists in roadmap
3. If no phase number, detect next unplanned phase from roadmap
4. Plan the phase:
   - Load project state and accumulated decisions
   - Perform mandatory discovery (read relevant source files, existing patterns, test setup)
   - Read project history (prior decisions, issues, concerns)
   - Break phase into tasks
   - Estimate scope and split into multiple plans if needed
   - Create PLAN.md file(s) with executable structure
</process>

<plan_structure>
Each PLAN.md must contain:

```markdown
---
phase: XX-name
plan: XX-YY
---

<objective>
[What this plan accomplishes - specific deliverable]
</objective>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
[Relevant source files]
</context>

<tasks>
<task type="auto|verify|decision">
  <name>[Task name]</name>
  <files>[Files to create/modify]</files>
  <action>
[Specific instructions for what to do]
  </action>
  <verify>[How to verify this task is complete]</verify>
  <done>[Acceptance criteria]</done>
</task>
</tasks>

<verification>
[Overall plan acceptance criteria]
</verification>

<success_criteria>
[What success looks like]
</success_criteria>

<output>
After completion, create SUMMARY.md for this plan.
</output>
```
</plan_structure>

<scope_guidelines>
- 2-3 tasks per plan is the ideal range
- If a phase has more work, split into multiple plans (XX-01, XX-02, etc.)
- Each plan should be independently executable in ~30-60 minutes
- If a task would touch >5 files, split it into sub-tasks
</scope_guidelines>

<success_criteria>

- One or more PLAN.md files created in .planning/phases/XX-name/
- Each plan has: objective, context, tasks, verification, success_criteria, output
- Tasks are specific enough for Claude to execute without asking questions
- User knows next steps (execute plan or review/adjust)
  </success_criteria>
