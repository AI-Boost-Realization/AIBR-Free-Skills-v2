---
name: gsd:verify-work
description: Guide manual user acceptance testing of recently built features
argument-hint: "[optional: phase or plan number, e.g., '4' or '04-02']"
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - Edit
  - Write
  - AskUserQuestion
---

<objective>
Guide the user through manual acceptance testing of recently built features.

Purpose: Validate that what Claude thinks was built actually works from the user's perspective. The USER performs all testing — Claude generates the test checklist, guides the process, and captures issues.

Output: Validation of features, any issues logged to phase-scoped ISSUES.md
</objective>

<context>
Scope: $ARGUMENTS (optional)
- If provided: Test specific phase or plan (e.g., "4" or "04-02")
- If not provided: Test most recently completed plan

**Load project state:**
@.planning/STATE.md

**Load roadmap:**
@.planning/ROADMAP.md
</context>

<process>
1. Validate arguments (if provided, parse as phase or plan number)
2. Find relevant SUMMARY.md (specified or most recent)
3. Follow verify workflow:
   - Extract testable deliverables from SUMMARY.md
   - Generate test checklist based on what was built
   - Guide through each test via AskUserQuestion
   - Collect and categorize issues (critical/major/minor)
   - Log issues to `.planning/phases/XX-name/{phase}-{plan}-ISSUES.md`
   - Present summary with verdict
4. Offer next steps based on results:
   - If all passed: Continue to next phase
   - If issues found: `/gsd:plan-fix {phase} {plan}` to create fix plan
</process>

<test_checklist_format>
For each deliverable from SUMMARY.md, generate a test item:

```
Test [N]: [Feature name]
Steps:
1. [Do this]
2. [Then this]
3. [Expect this result]

Expected outcome: [What should happen]
```
</test_checklist_format>

<issue_format>
When user reports an issue, capture it as:

```markdown
### UAT-[N]: [Issue title]
**Severity:** critical | major | minor
**Steps to reproduce:**
1. [Step]
2. [Step]
**Expected:** [What should happen]
**Actual:** [What happened]
**Acceptance criteria:** [What "fixed" looks like]
```
</issue_format>

<anti_patterns>
- Don't run automated tests (that's for CI/test suites)
- Don't make assumptions about test results — USER reports outcomes
- Don't skip the guidance — walk through each test
- Don't dismiss minor issues — log everything user reports
- Don't fix issues during testing — capture for later
</anti_patterns>

<success_criteria>
- [ ] Test scope identified from SUMMARY.md
- [ ] Checklist generated based on deliverables
- [ ] User guided through each test
- [ ] All test results captured (pass/fail/partial/skip)
- [ ] Any issues logged to phase-scoped ISSUES.md (not global)
- [ ] Summary presented with verdict
- [ ] User knows next steps based on results
</success_criteria>
