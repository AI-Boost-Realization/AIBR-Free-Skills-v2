# Meridian API

Meridian is a multi-tenant SaaS API that handles real-time event ingestion, fan-out processing, and webhook delivery for B2B customers. The backend is TypeScript running on Hono, backed by PostgreSQL (Neon serverless) and Redis (Upstash) for queue management. Deployed to Railway. The codebase is about 40k lines across the API server, a background worker, and a shared types package.

---

## Stack

- **Runtime**: Node.js 20 (TypeScript strict mode throughout)
- **Framework**: Hono — static routes must be declared before parameterized ones (`/webhooks/test` before `/webhooks/:id`)
- **Database**: PostgreSQL via Neon serverless driver. All queries use parameterized statements; no raw string interpolation
- **Queue**: Upstash Redis + BullMQ for fan-out jobs
- **Auth**: JWT with RS256. Public key loaded from env at startup — never hardcoded
- **Deploy**: Railway (auto-deploy on merge to `main` via GitHub integration)
- **Test**: Vitest with real Neon branch per test run (not mocked DB — prior mock divergence caused a prod incident)

---

## Model Routing

Route each task to the appropriate model tier. Default to Sonnet when uncertain.

| Task type | Model | Reason |
|-----------|-------|--------|
| Architecture decisions, security review, multi-file refactor (10+ files) | Opus | Decisions are expensive to reverse |
| Feature implementation, bug fixes, API integration, 1-10 file edits | Sonnet | Standard implementation complexity |
| Search, grep, file reads, dependency audits, doc writes | Haiku | Speed over depth; no judgment needed |
| Any task touching auth, credentials, or billing | Opus minimum | Security-sensitive path |

In practice: spawn `explorer` (Haiku) to map the surface, `builder` (Sonnet) to implement, `verifier` (Sonnet) to test, `security-reviewer` (Opus) if anything touches auth or billing paths.

---

## Active Hooks

These hooks are wired in `~/.claude/settings.json`. Do not disable without understanding the consequence.

| Hook file | Event | What it does |
|-----------|-------|--------------|
| `inject-git-state.sh` | SessionStart | Injects current branch, last 5 commits, and dirty status into every session |
| `env-blocker.sh` | PreToolUse (Write) | Blocks all writes to `.env*` files — edit manually |
| `git-safety-check.sh` | PreToolUse (Bash) | Warns before force-push or push directly to `main`; suggests PR |
| `secret-scanner.md` (hookify) | PreToolUse (Bash on `git add`) | Scans staged diff for API key patterns before staging |
| `auto-diagnose.sh` | PostToolUse (Bash) | Categorizes non-zero exits — auth errors, rate limits, build failures — and suggests a first step |
| `post-edit-typecheck.sh` | PostToolUse (Write/Edit) | Runs `tsc --noEmit` after any TypeScript file edit |
| `memory-extract.sh` | Stop | Sends last N tool calls to Haiku for session insight extraction; writes to memory pipeline |

If `post-edit-typecheck.sh` fires and TypeScript fails, fix the type error before proceeding. Do not suppress with `@ts-ignore` without a justification comment.

---

## Agent Delegation

Use the right agent for the scope. Orchestrator is overkill for 1-2 file edits.

| Situation | Agent to use |
|-----------|-------------|
| 1-2 file edits, clear task | `builder` (Sonnet, direct dispatch) |
| Feature spanning 3+ files | `orchestrator` (Opus) — decomposes and dispatches builders |
| Tests failing after an edit | `verifier` (Sonnet) — never `builder` |
| Read-only investigation | `explorer` (Haiku) |
| Deployment to Railway | `deployer` (Sonnet) — after verifier passes |
| Security or auth changes | `security-reviewer` (Opus) — mandatory review before merge |
| Documentation | `scribe` (Haiku) |

The orchestrator writes a plan to `~/.claude/shared-state/saved-plan.md` before dispatching any builders. Do not bypass this step on complex tasks — unplanned builds cause collisions.

---

## GSD Integration

This project was scaffolded using `/gsd:new-project`. The project plan lives at `~/.claude/shared-state/saved-plan.md`. Phase and milestone state is tracked automatically.

- `/progress` — shows current phase completion %
- `/next` — surfaces the single highest-priority next action
- `/resume-work` — picks up where the last session left off after compaction

When starting a new session on this project: run `/go` first. It loads active context, checks for in-progress tasks, and runs a preflight (branch, env, tests) before any implementation work begins.

---

## Memory System

`memory-extract.sh` runs automatically at session end (Stop hook). It sends the last tool calls to Haiku with an extraction prompt that identifies:
- Non-obvious decisions worth preserving
- Behavioral changes (hooks, routing, patterns)
- Surprises that cost time to discover

Extracted memories are written to `~/.claude/memory/` and indexed in `MEMORY.md`. Future sessions load the index at startup. You get compound memory without running `/session-end` manually.

Do not delete or overwrite files in `~/.claude/memory/` — the memory pipeline appends, not replaces.

---

## Key Conventions

1. **No raw SQL string interpolation.** All queries use parameterized placeholders. A linter rule enforces this — do not suppress it.
2. **Static routes before parameterized routes in Hono.** `app.get('/webhooks/test', ...)` must be declared before `app.get('/webhooks/:id', ...)`. Getting this wrong causes silent routing bugs.
3. **No `git add -A` or `git add .`** in automation. Always stage specific files. The secret scanner hook can't protect you from blindly staged credential files.
4. **Real DB in tests, not mocks.** Every test run provisions a fresh Neon branch via the test setup hook. Mocks are banned — see `vitest.config.ts` for the setup file.
5. **Pre-commit hooks are required.** If `git commit` fails, read the hook output and fix it. Do not bypass with `--no-verify`.
