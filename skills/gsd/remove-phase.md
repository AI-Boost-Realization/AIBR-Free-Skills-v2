---
name: gsd:remove-phase
description: Remove a future phase from roadmap and renumber subsequent phases
argument-hint: <phase-number>
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

<objective>
Remove an unstarted future phase from the roadmap and renumber all subsequent phases to maintain a clean, linear sequence.

Purpose: Clean removal of work you've decided not to do, without polluting context with cancelled/deferred markers.
Output: Phase deleted, all subsequent phases renumbered, git commit as historical record.
</objective>

<execution_context>
@.planning/ROADMAP.md
@.planning/STATE.md
</execution_context>

<process>

<step name="parse_arguments">
Parse the command arguments:
- Argument is the phase number to remove (integer or decimal)
- Example: `/gsd:remove-phase 17` → phase = 17
- Example: `/gsd:remove-phase 16.1` → phase = 16.1

If no argument provided, exit with usage error.
</step>

<step name="load_state">
Load project state:

```bash
cat .planning/STATE.md 2>/dev/null
cat .planning/ROADMAP.md 2>/dev/null
```

Parse current phase number from STATE.md "Current Position" section.
</step>

<step name="validate_phase_exists">
Verify the target phase exists in ROADMAP.md:

1. Search for `### Phase {target}:` heading
2. If not found, exit with error listing available phases.
</step>

<step name="validate_future_phase">
Verify the phase is a future phase (not started):

1. Compare target phase to current phase from STATE.md
2. Target must be > current phase number

If target <= current phase:
```
ERROR: Cannot remove Phase {target}

Only future phases can be removed:
- Current phase: {current}
- Phase {target} is current or completed

To abandon current work, use /gsd:pause-work instead.
```

3. Check for SUMMARY.md files in phase directory — cannot remove phases with completed work.
</step>

<step name="gather_phase_info">
Collect information about the phase being removed:

1. Extract phase name from ROADMAP.md heading: `### Phase {target}: {Name}`
2. Find phase directory: `.planning/phases/{target}-{slug}/`
3. Find all subsequent phases (integer and decimal) that need renumbering

**Subsequent phase detection:**

For integer phase removal (e.g., 17):
- Find all phases > 17 (integers: 18, 19, 20...)
- Find all decimal phases >= 17.0 and < 18.0 → these become 16.x
- Find all decimal phases for subsequent integers → renumber with their parent

For decimal phase removal (e.g., 17.1):
- Find all decimal phases > 17.1 and < 18 (17.2, 17.3...) → renumber down
- Integer phases unchanged
</step>

<step name="confirm_removal">
Present removal summary and confirm:

```
Removing Phase {target}: {Name}

This will:
- Delete: .planning/phases/{target}-{slug}/
- Renumber {N} subsequent phases:
  - Phase 18 → Phase 17
  - Phase 19 → Phase 18
  [etc.]

Proceed? (y/n)
```

Wait for confirmation.
</step>

<step name="delete_phase_directory">
Delete the target phase directory if it exists:

```bash
if [ -d ".planning/phases/{target}-{slug}" ]; then
  rm -rf ".planning/phases/{target}-{slug}"
  echo "Deleted: .planning/phases/{target}-{slug}/"
fi
```
</step>

<step name="renumber_directories">
Rename all subsequent phase directories in descending order (to avoid overwriting):

```bash
# Example: renaming 18-dashboard to 17-dashboard
mv ".planning/phases/18-dashboard" ".planning/phases/17-dashboard"
```

Process in descending order (20→19, then 19→18, then 18→17).

Also rename decimal phase directories accordingly.
</step>

<step name="rename_files_in_directories">
Rename plan files inside renumbered directories:

```bash
# Inside 17-dashboard (was 18-dashboard):
mv "18-01-PLAN.md" "17-01-PLAN.md"
mv "18-02-PLAN.md" "17-02-PLAN.md"
# etc.
```
</step>

<step name="update_roadmap">
Update ROADMAP.md:

1. **Remove the phase section entirely** (from `### Phase {target}:` to next phase heading)
2. **Renumber all subsequent phases** in headings, lists, tables, and dependency references
3. Write updated ROADMAP.md
</step>

<step name="update_state">
Update STATE.md:

1. Update total phase count
2. Recalculate progress percentage

Do NOT add a "Roadmap Evolution" note — the git commit is the record.
</step>

<step name="commit">
Stage and commit the removal:

```bash
git add .planning/
git commit -m "chore: remove phase {target} ({original-phase-name})"
```

The commit message preserves the historical record of what was removed.
</step>

<step name="completion">
Present completion summary:

```
Phase {target} ({original-name}) removed.

Changes:
- Deleted: .planning/phases/{target}-{slug}/
- Renumbered: Phases {first}-{last-old} → {first-1}-{last-new}
- Updated: ROADMAP.md, STATE.md
- Committed: chore: remove phase {target} ({original-name})

Current roadmap: {total-remaining} phases
Current position: Phase {current} of {new-total}
```
</step>

</process>

<anti_patterns>

- Don't remove completed phases (have SUMMARY.md files)
- Don't remove current or past phases
- Don't leave gaps in numbering - always renumber
- Don't add "removed phase" notes to STATE.md - git commit is the record
- Don't ask about each decimal phase - just renumber them
- Don't modify completed phase directories
</anti_patterns>

<edge_cases>

**Removing a decimal phase (e.g., 17.1):**
- Only affects other decimals in same series (17.2 → 17.1, 17.3 → 17.2)
- Integer phases unchanged

**No subsequent phases to renumber:**
- Just delete and update ROADMAP.md, no renumbering needed

**Phase directory doesn't exist:**
- Phase may be in ROADMAP.md but directory not created yet
- Skip directory deletion, proceed with ROADMAP.md updates

</edge_cases>

<success_criteria>
Phase removal is complete when:

- [ ] Target phase validated as future/unstarted
- [ ] Phase directory deleted (if existed)
- [ ] All subsequent phase directories renumbered
- [ ] Files inside directories renamed
- [ ] ROADMAP.md updated (section removed, all references renumbered)
- [ ] STATE.md updated (phase count, progress percentage)
- [ ] Changes committed with descriptive message
- [ ] No gaps in phase numbering
- [ ] User informed of changes
</success_criteria>
