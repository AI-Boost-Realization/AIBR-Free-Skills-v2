# Contributing

This document covers how to add skills, agents, and hooks to the AIBR framework. Keep contributions focused, self-contained, and grounded in real production use.

---

## Adding a Skill

Skills live in `skills/<category>/skill-name.md`. The installer symlinks everything under `skills/` into `~/.claude/commands/`, so the file name becomes the slash command.

**Required frontmatter:**

```markdown
---
name: skill-name
description: One sentence — what it does and when to use it
allowed-tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
user_invocable: true
argument-hint: "[optional: describe accepted arguments]"
---
```

- `name` must match the filename (without `.md`)
- `description` is what shows up in `/help` listings — make it scannable
- `allowed-tools` is the explicit allowlist; only include tools the skill actually needs
- `user_invocable: true` means the skill appears as a slash command; set `false` for internal-only skills

**Where to put it:**

Place the file under the most specific existing category: `debugging/`, `git/`, `code-quality/`, `planning/`, `productivity/`, `multi-agent/`, `knowledge/`, `research/`, `deployment/`, `gsd/`. Create a new category folder only if none of the existing ones fit — and update the README table.

**How the installer picks it up:**

`install.sh` recurses through `skills/` and symlinks every `.md` file. No registration step needed. Run `./install.sh --dry-run` to preview.

---

## Adding an Agent

Agents live in `agents/agent-name.md`. The installer symlinks them into `~/.claude/agents/`.

**Required frontmatter:**

```markdown
---
name: agent-name
description: One sentence — role and scope
model: claude-sonnet-4-5-20251001
tools: Read, Glob, Grep, Bash, Write, Edit
disallowedTools: EnterWorktree, ExitWorktree
maxTurns: 25
---
```

**Model tier guidance** (from `patterns/model-routing.md`):

| Role type | Model to use |
|-----------|-------------|
| Architecture, security review, orchestration, planning | `claude-opus-4-5` (Opus) |
| Implementation, testing, deployment, code review | `claude-sonnet-4-5-20251001` (Sonnet) |
| Search, read-only investigation, doc writing, diagnostics | `claude-haiku-4-5-20251001` (Haiku) |

Set `disallowedTools` explicitly. An agent that is not allowed to write files should list `Write, Edit` in `disallowedTools`. Narrow scope produces more reliable output.

---

## Adding a Hook

Hooks live in `hooks/<event>/hook-name.sh` (or `.md` for hookify-style declarative rules).

**Shell script hooks:**

- Must be executable (`chmod +x`)
- Output `{"decision": "block", "reason": "..."}` to block the tool (PreToolUse only)
- Output `{"prompt": "..."}` to inject context into Claude's next response
- Exit 0 with no output for silent success (zero context cost)
- Hook failures (non-zero exit without a block decision) surface to Claude but do not block

**Hookify declarative hooks:**

Use the frontmatter format from `configs/hookify-templates/` for simple warn/block rules. See `configs/hookify-templates/README.md` for when this is appropriate vs. a shell script.

**Wiring into settings.json:**

The installer prints the exact JSON snippet to paste. Manual wiring follows the pattern in `patterns/hook-lifecycle.md`. The `matcher` field filters by tool name; omit it to fire on all tool calls.

---

## Code Quality Bar

Before submitting, ask: does this skill or agent solve a real problem that cost real time to discover? The bar is production use, not hypothetical utility.

A good contribution:
- Works end-to-end on a real project without modification
- Is self-contained — all logic is in the file, no undocumented external dependencies
- Contains no hardcoded paths (no `/Users/yourname/...`)
- Contains no client-specific details, personal tokens, or internal hostnames
- Follows the step-by-step format of existing skills (see `skills/debugging/quick-debug.md`)

A contribution that will be rejected:
- Wraps another tool with no added value
- Requires manual setup steps not documented in the file
- References personal or organizational infrastructure

---

## PR Process

1. Fork the repo and create a branch: `feature/skill-name` or `fix/hook-name`
2. Add your skill, agent, or hook following the conventions above
3. Run `./install.sh --dry-run` and confirm your file appears in the preview output with no errors
4. Update the relevant README table (top-level `README.md` or the category's own README if it exists)
5. Submit a PR with a one-paragraph description: what problem it solves, where it came from (real project use preferred), and any known limitations

PRs that skip `--dry-run` verification or add README entries will be returned for revision.
