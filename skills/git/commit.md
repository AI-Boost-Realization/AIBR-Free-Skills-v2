---
name: commit
description: Stage changes intelligently, generate a semantic commit message from the diff, handle pre-commit hook failures without losing work
allowed-tools: ["Bash", "Read", "Glob"]
user_invocable: true
argument-hint: "[--amend] [--all] [message override]"
---

# Commit

Create a clean, well-scoped commit from the current working tree. Stages the right files, generates a conventional commit message from the actual diff, and recovers from pre-commit hook failures without losing work.

## When to Use

- After completing a feature, fix, or refactor and you want a precise commit message without writing boilerplate
- When you have multiple changed files and need to stage only the relevant ones
- When a pre-commit hook failed and you need to recover cleanly (never `--amend` after a failed hook)
- As a direct alias: `/commit` stages, messages, and commits in one pass

## Arguments

- `--all` — stage all tracked changed files (equivalent to `git add -u`). Untracked files are reported but not staged.
- `--amend` — amend the previous commit instead of creating a new one. Only use when the previous commit has NOT been pushed.
- `[message override]` — if a message is provided as the argument, skip message generation and use it directly (still runs pre-commit hooks).

## Process

### Step 1 — Understand Current State

```bash
git status
git diff --staged
```

If nothing is staged, also run:
```bash
git diff --stat
```

Report:
- How many files are staged vs. unstaged vs. untracked
- Whether untracked files look like they belong in this commit
- Any files that look like they should NOT be committed (build artifacts, `.env`, binaries)

### Step 2 — Stage Specific Files (if nothing is staged)

Do NOT run `git add -A` or `git add .`. Stage file by file based on relevance:

```bash
git add src/specific/file.ts src/another/file.ts
```

Categorize every changed file into one of three buckets before staging:

| Bucket | Action |
|--------|--------|
| Related to the current task | Stage it |
| Unrelated change mixed in | Leave unstaged — mention it in the report |
| Should never be committed (.env, secrets, large binaries) | Warn the user, do not stage |

If `--all` was passed, run `git add -u` to stage all tracked modifications and deletions, then continue to Step 3.

### Step 3 — Determine Commit Type

Read the staged diff:
```bash
git diff --staged
```

Classify the change using conventional commit prefixes:

| Prefix | When to use |
|--------|-------------|
| `feat` | New capability visible to users or callers |
| `fix` | Corrects a bug in existing behavior |
| `refactor` | Internal restructuring — no behavior change |
| `chore` | Tooling, deps, config — no production code change |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |

If the diff spans multiple types (e.g., a fix and a refactor), commit separately if practical. If not, use the dominant type.

### Step 4 — Generate the Commit Message

Construct the message following conventional commits format:

```
<type>(<optional scope>): <subject>

<optional body — 2-4 lines, explains WHY not WHAT>

Co-Authored-By: Claude Code <noreply@anthropic.com>
```

Rules:
- Subject: imperative mood, present tense, max 72 characters, no trailing period
- Scope: optional, the module or area affected (`auth`, `api`, `worker`, `db`)
- Body: only when the why is non-obvious. The diff shows the what; the body explains the why.

If a message override was provided as an argument, use it as the subject and skip generation.

### Step 5 — Commit

```bash
git commit -m "$(cat <<'EOF'
<generated message>

Co-Authored-By: Claude Code <noreply@anthropic.com>
EOF
)"
```

**If the commit succeeds:** show the result and stop.

```bash
git log --oneline -1
git show --stat HEAD
```

**If a pre-commit hook fails:**

1. Read the full hook output — identify exactly what it flagged (lint errors, type errors, format violations, secret patterns)
2. Do NOT use `--no-verify` to bypass unless the user explicitly instructs it
3. Fix the flagged issues (lint, format, type errors)
4. Re-stage the affected files:
   ```bash
   git add <files that were fixed>
   ```
5. Create a NEW commit — do not `--amend`. Amending after a failed hook risks modifying the wrong commit. The failed commit did not land, so there is no "previous commit" to amend.

### Step 6 — Report Unstaged Remainder

After a successful commit, report any files that were intentionally left unstaged:

```
Left unstaged (separate concern or not for this commit):
  - src/utils/logger.ts — unrelated formatting cleanup
  - .env.local — never commit secrets
```

This keeps the user informed of their working tree state without cluttering the commit.

## Edge Cases

**Nothing to commit:** If both `git status` and `git diff` show a clean working tree, report it clearly and stop.

**Detached HEAD:** Warn the user before committing — commits in detached HEAD state are not reachable from any branch.

**Binary files staged:** Warn before including images, compiled artifacts, or other binaries. Confirm with user.

**Merge in progress:** If `.git/MERGE_HEAD` exists, the commit will complete a merge. Note this in the report.
