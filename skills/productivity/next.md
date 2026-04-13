---
name: next
description: "Intelligent work continuation — shows what's done, what's in progress, what's blocked, and what to do next. Pushes through blockers using SDLC best practices. Use when the user says '/next', 'what's next', 'continue', 'keep going', 'what should I do', 'show progress', 'push through', 'unblock me', or any time they want to advance work on the current project."
priority: high
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Write
  - Edit
  - Agent
  - Skill
---

<objective>
Push work forward. `/next` reads every available context source — session state, plans, git status, codebase — builds a complete picture of where things stand, and then recommends and executes the most impactful next action.
</objective>

<process>

<step name="gather_context">
**Gather the most current context from ALL sources — never rely on stale data:**

1. Read git state fresh:
```bash
git log --oneline -5 2>/dev/null
git status 2>/dev/null
```

2. Read session state:
   - Check for a current work session file or saved plan — `next_action` and `completed_this_session` are authoritative.

3. Read plan files if any exist:
```bash
ls -t *.md .planning/*.md 2>/dev/null | head -5
```

4. Collect TODO/outstanding items from ALL sources:
   - Session state `next_action` field
   - Plan file outstanding/unchecked items
   - Git uncommitted changes that need attention

The goal: every item presented should be current and verified against real state.
</step>

<step name="update_state_before_display">
**Before showing anything, update plans to reflect current reality:**

1. If the `next_action` from the session file has already been completed (check git commits), update it to the actual next action.

2. If an active plan file exists:
   - Mark items as completed if git commits confirm they're done
   - Flag items as blocked if new blockers were found

3. Compile the master TODO list:
   - Sort by: deadline urgency > priority > effort (quick wins first)
   - Note which items are parallelizable vs sequential
   - Flag items outstanding for >24h
</step>

<step name="check_sdlc_state">
**Detect where we are in the development lifecycle:**

| Signal | SDLC Phase | What to Suggest |
|--------|------------|-----------------|
| Plan just approved, no code changes | **Start implementing** | Begin with step 1 of the plan |
| Uncommitted code changes exist | **Test and validate** | Run tests, type check, or manual verification |
| Tests passing, changes uncommitted | **Commit** | Stage and commit with descriptive message |
| Recent commit, no deployment | **Deploy and verify** | Deploy to staging/production + health check |
| Deploy complete, not verified | **Verify** | Check endpoints, logs, or browser |
| Verification failed | **Debug** | Check logs, identify root cause |
| Everything green, plan has more steps | **Next plan step** | Move to next uncompleted item |
| All plan steps done | **Review and ship** | PR, final review, or mark milestone complete |

Also check:
- Modified test files → tests were being worked on
- Recent commits mention "fix" or "debug" → in a debug cycle
- TODO comments in recently modified files → surface them
</step>

<step name="check_blockers">
**Identify and suggest workarounds for blockers:**

For each blocker, suggest a resolution strategy:
- **External dependency blocked?** → Skip to an independent task
- **Missing credentials?** → Check `.env`, note where to get them
- **Test failing?** → Run the specific failing test, show the error
- **Build broken?** → Check error output, suggest fix
- **Waiting on human input?** → Flag it, move to next independent task
</step>

<step name="render_dashboard">
**Display the progress dashboard:**

Parse arguments:
- `--status` → Show dashboard only, do NOT execute any actions
- `--skip` → Skip the first recommended action, show the second
- `--blocker` → Focus entirely on resolving the top blocker
- No args → Show dashboard AND execute the recommended next action

```
/next ══════════════════════════════════════════════════
  {project_name} | {current_time}

  DONE (this session)
  [x] {completed item}
  [x] {completed item}

  IN PROGRESS
  --> {what is currently being worked on}

  BLOCKED
  [!] {blocker} → {suggested workaround}

  NEXT STEP
  [>] {specific, actionable next step}
      Why: {one-line reasoning}
      Est: {rough effort estimate}

  OUTSTANDING ({count} remaining)
  [ ] {next 3-5 uncompleted items}

  SUGGESTED
  [*] {intelligent suggestion from codebase analysis}
════════════════════════════════════════════════════════
```

Adapt sections based on available data:
- No active plan? Skip OUTSTANDING, focus on codebase-sourced suggestions
- No blockers? Skip BLOCKED section
- Late night? Add a note to commit current work before wrapping up
</step>

<step name="execute_next">
**Unless `--status` was passed, execute the recommended next action immediately.**

The action depends on the SDLC phase detected:

**If implementing:** Start coding the next plan step. Read relevant files, make the changes.

**If testing:** Run the test suite or perform manual verification.
```bash
npm test  # or pytest, cargo test, etc.
```

**If committing:** Stage relevant files and prepare a commit message.

**If deploying:** Run the project's deploy command.

**If debugging:** Read error logs, identify root cause, propose fix.

**If blocked:** Skip to the next independent task from the plan.

**If all done:** Suggest next steps — check for uncommitted work, look for other active work items.
</step>

</process>

<intelligence_rules>

## Time-Aware Behavior

| Time Period | Behavior |
|-------------|----------|
| **Morning (6-12)** | "Good morning. Yesterday you completed X. Resuming from Y." |
| **Afternoon (12-17)** | Standard execution mode. Push through work. |
| **Evening (17-21)** | Note progress made today. If many items done, suggest wrapping up. |
| **Late night (21-6)** | Bias toward commit/save over starting new tasks. |

## Blocker Resolution Priority

1. **Self-resolvable** (missing file, wrong branch) → Fix immediately
2. **Workaround available** (blocked API, missing creds) → Skip to independent task
3. **Needs human input** (design decision, credential) → Flag clearly, move on
4. **Hard block** (everything depends on this) → Escalate with full context

## SDLC Best Practices Enforcement

- Never suggest deploying without testing
- Never suggest committing without reviewing changes
- After code changes, always suggest verification
- After deployment, always suggest health checks
- Surface TODO/FIXME comments in recently changed files

</intelligence_rules>

<flags>

## Argument Handling

| Flag | Behavior |
|------|----------|
| (none) | Full dashboard + execute next step |
| `--status` | Dashboard only, read-only, no execution |
| `--skip` | Skip recommended next step, show alternative |
| `--blocker` | Focus on resolving the top blocker |
| `--force` | Execute next step even if blockers exist |

</flags>
