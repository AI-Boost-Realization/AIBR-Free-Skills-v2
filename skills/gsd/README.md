# GSD — Get Shit Done Framework

GSD is a complete AI project management framework with 22 commands, designed for managing complex multi-phase software projects using Claude Code.

Built from 12 months of real project management experience across production applications, it solves the core problem of AI-assisted development: Claude is excellent at executing individual tasks but lacks the scaffolding to track state, sequence work, and maintain context across sessions.

GSD provides that scaffolding.

---

## What It Does

GSD organizes all work into a hierarchy stored in your repository:

```
Project → Milestones → Phases → Plans → Tasks
```

- **Project**: The overall vision, requirements, and constraints
- **Milestone**: A shippable chunk of work (v1.0, v2.0, etc.)
- **Phase**: A focused area of work within a milestone (e.g., "Auth System", "API Layer")
- **Plan**: A concrete set of 2-3 tasks Claude executes autonomously
- **Task**: A single atomic unit of work with a commit

All state lives in `.planning/` inside your project, committed to git. Sessions are stateless — Claude reads the files, understands where you are, and picks up exactly where you left off.

---

## Command Tree

```
Initialization
  /gsd:new-project          Initialize project with deep context gathering
  /gsd:create-roadmap       Create roadmap and phase structure
  /gsd:map-codebase         Analyze existing codebase (brownfield projects)

Phase Planning
  /gsd:discuss-phase        Gather your vision for a phase before planning
  /gsd:research-phase       Research niche/complex domains before planning
  /gsd:list-phase-assumptions  See Claude's assumptions before planning starts
  /gsd:plan-phase           Generate executable PLAN.md for a phase

Execution
  /gsd:execute-plan         Execute a PLAN.md with per-task commits
  /gsd:resume-task          Resume an interrupted subagent execution

Roadmap Management
  /gsd:add-phase            Add phase to end of current milestone
  /gsd:insert-phase         Insert urgent decimal phase (e.g., 5.1 between 5 and 6)
  /gsd:remove-phase         Remove a future phase and renumber subsequent phases

Milestone Management
  /gsd:discuss-milestone    Figure out what to build in the next milestone
  /gsd:new-milestone        Create a new milestone with phases
  /gsd:complete-milestone   Archive completed milestone and create git tag

Progress & Session
  /gsd:progress             Check progress and route to next action
  /gsd:resume-work          Resume from previous session with full context
  /gsd:pause-work           Create a handoff file before stopping

Issue Management
  /gsd:consider-issues      Review deferred issues with codebase context
  /gsd:plan-fix             Create fix plan from UAT issues
  /gsd:verify-work          Guide user through manual acceptance testing

Reference
  /gsd:help                 Show full command reference
```

---

## Typical Workflow

### Starting a New Project

```
/gsd:new-project       ← Deep questioning, creates PROJECT.md
/gsd:create-roadmap    ← Phase breakdown, creates ROADMAP.md
/gsd:plan-phase 1      ← Generates PLAN.md for Phase 1
/gsd:execute-plan .planning/phases/01-foundation/01-01-PLAN.md
```

### Daily Work Loop

```
/gsd:progress          ← See where you are, get routed to next action
/gsd:execute-plan ...  ← Execute the next plan
/gsd:progress          ← Check what's next, repeat
```

### Resuming After a Break

```
/gsd:resume-work       ← Full context restoration + smart routing
```

### Handling Unexpected Work

```
/gsd:insert-phase 5 "Fix critical auth bug"   ← Creates Phase 5.1
/gsd:plan-phase 5.1
/gsd:execute-plan .planning/phases/05.1-.../05.1-01-PLAN.md
```

### Completing a Milestone

```
/gsd:verify-work       ← User acceptance testing
/gsd:complete-milestone 1.0.0    ← Archive, git tag, prepare for next
/gsd:discuss-milestone ← Figure out what to build next
/gsd:new-milestone "v2.0 Features"
```

---

## File Structure

```
.planning/
├── PROJECT.md            # Project vision, requirements, constraints
├── ROADMAP.md            # All milestones and phases with status
├── STATE.md              # Living project memory — current position, decisions, issues
├── ISSUES.md             # Deferred enhancements (auto-created when needed)
├── MILESTONES.md         # Index of completed milestones
├── config.json           # Workflow mode (interactive/yolo) and planning depth
├── codebase/             # Codebase map for brownfield projects
│   ├── STACK.md
│   ├── ARCHITECTURE.md
│   ├── STRUCTURE.md
│   ├── CONVENTIONS.md
│   ├── TESTING.md
│   ├── INTEGRATIONS.md
│   └── CONCERNS.md
├── milestones/
│   └── v1.0-ROADMAP.md  # Archived milestone details
└── phases/
    ├── 01-foundation/
    │   ├── 01-01-PLAN.md
    │   ├── 01-01-SUMMARY.md
    │   └── 01-CONTEXT.md    # Optional: vision captured before planning
    └── 02-api-layer/
        ├── 02-01-PLAN.md
        ├── 02-01-SUMMARY.md
        ├── 02-02-PLAN.md
        └── 02-02-SUMMARY.md
```

---

## Workflow Modes

Set at project initialization, changeable anytime in `.planning/config.json`:

**Interactive**: Claude confirms major decisions, pauses at checkpoints. Good for early phases or unfamiliar domains.

**YOLO**: Claude auto-approves most decisions, executes without confirmation. Good once you trust the flow.

---

## Design Principles

**State lives in git, not in Claude's context.** Every session reads fresh from files. Context window can be cleared between phases — GSD tracks where you are so you don't have to.

**Per-task commits, not big-bang commits.** Each task gets its own commit immediately on completion. This makes rollbacks surgical and keeps history meaningful.

**User is the visionary, Claude is the builder.** `discuss-phase` and `discuss-milestone` surface your vision — Claude reads the code and figures out the technical approach.

**Scope by estimation, not by formula.** Plans target 2-3 tasks. If a phase has more work, it gets split into multiple plans. Comprehensive depth means "don't compress complex work," not "pad simple work."

**Issues are deferred, not forgotten.** When Claude discovers nice-to-haves during execution, they go to ISSUES.md, not into scope. `consider-issues` lets you triage them with fresh codebase context later.
