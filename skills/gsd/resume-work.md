---
name: gsd:resume-work
description: Resume work from previous session with full context restoration
allowed-tools:
  - Read
  - Bash
  - Write
  - AskUserQuestion
  - SlashCommand
---

<objective>
Restore complete project context and resume work seamlessly from previous session.

Handles:
- STATE.md loading (or reconstruction if missing)
- Checkpoint detection (.continue-here files)
- Incomplete work detection (PLAN without SUMMARY)
- Status presentation
- Context-aware next action routing
  </objective>

<process>

1. **Verify project exists:**
   - Check for `.planning/` directory
   - If missing: `No planning structure found. Run /gsd:new-project to start.`

2. **Load or reconstruct STATE.md:**
   - Read `.planning/STATE.md` for current position, decisions, issues
   - If STATE.md is missing or corrupt, reconstruct from ROADMAP.md and phase directories

3. **Detect checkpoints and incomplete work:**
   - Check for `.continue-here.md` files in any phase directory
   - Check for PLAN.md files without matching SUMMARY.md (incomplete execution)
   - Check for ISSUES.md files without matching FIX.md (unaddressed UAT issues)

4. **Present status:**
   ```
   ## Resuming: [Project Name]

   **Current position:** Phase [N]: [Phase Name]
   **Progress:** [X/Y plans complete]

   **Recent work:**
   - [Last completed plan and what it did]

   **Incomplete work found:**
   - [Any .continue-here.md files]
   - [Any unexecuted PLAN.md files]
   ```

5. **Offer context-aware next actions** using AskUserQuestion:
   - If .continue-here.md exists: "Resume in-progress work" (top option)
   - If unexecuted PLAN.md exists: "Execute next plan"
   - If phase needs planning: "Plan next phase" or "Discuss phase first"
   - Always: "Check progress overview" (/gsd:progress)

6. **Update session continuity in STATE.md**

</process>

<success_criteria>

- Project context fully loaded
- Checkpoints and incomplete work detected
- Status presented clearly
- Context-aware options offered (checks CONTEXT.md before suggesting plan vs discuss)
- User routed to appropriate next command
  </success_criteria>
