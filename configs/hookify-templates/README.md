# Hookify Templates

## What is Hookify?

Hookify is a Claude Code plugin that converts natural language rules into `PreToolUse` hooks wired directly into your `settings.json`. Instead of writing shell scripts manually, you describe what to block or warn about in plain English — hookify generates the hook configuration and handles the settings wiring. Rules live as simple markdown files with YAML frontmatter.

See the [hookify plugin directory](../../plugins/) for the plugin source, and `patterns/hook-lifecycle.md` for how hooks fit into the broader Claude Code runtime.

---

## The 5 Templates

| File | What it blocks or warns | When to use it |
|------|------------------------|----------------|
| `branch-protection.md` | Direct pushes and force-pushes to `main` or `master` | Any project where `main` should only accept PRs |
| `secret-scanner.md` | Staged files containing API keys, bearer tokens, or connection string credentials | Always — secrets in git history are unrecoverable |
| `disk-space-guard.md` | `npm install`, `pip install`, `docker build` when disk is below 5 GB | Projects with large dependency trees or Docker images |
| `retry-limit.md` | Runaway retry loops — same command failing 3+ times in a row | Debugging sessions, autonomous agents, CI-like workflows |
| `typescript-lint.md` | TypeScript file edits that leave the compiler in a broken state | TypeScript projects where type safety is non-negotiable |

---

## How to Apply a Template

### Option 1 — via the hookify command (recommended)

If the hookify plugin is installed:

```
/hookify apply branch-protection
```

Hookify reads the template, generates the hook config, and patches your `settings.json` automatically.

### Option 2 — manual copy

1. Copy the template file to your project's `.claude/hooks/` directory (or `~/.claude/hooks/` for global scope)
2. Open your `settings.json` and add the hook under the appropriate event key:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "type": "command",
        "command": "~/.claude/hooks/pre-tool/branch-protection.sh"
      }
    ]
  }
}
```

The `matcher` field filters by tool name. Use `"Bash"` for shell command hooks, `"Write"` for file write hooks. Omit `matcher` to run on every tool call.

See `patterns/hook-lifecycle.md` for the complete wiring reference and output format documentation.

---

## When NOT to Use Hookify

Hookify is the right tool for rules that need to run automatically on every matching tool call. Use a skill or agent instead when:

- **The rule requires multi-step logic** — e.g., "check if the branch is clean, then run tests, then deploy." That is a skill (`/deploy`), not a hook.
- **The rule is optional or user-invoked** — hooks fire whether you want them to or not. If the user should consciously opt in each time, make it a skill.
- **The rule needs to make decisions based on context** — hooks operate on the raw tool call. If the decision depends on the current task, project state, or user intent, delegate to an agent.
- **The rule produces output the user needs to act on** — hooks inject a prompt or block silently. If you need a structured report, a skill with `Read`/`Write` access is more appropriate.

A good hookify rule is short, stateless, and fires on a well-defined trigger. If you are writing more than 10 lines of logic into a hookify template body, it probably belongs in a shell script hook instead (see `hooks/pre-tool/` for examples).
