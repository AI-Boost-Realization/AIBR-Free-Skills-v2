# AIBR Agent Framework

[![CI](https://github.com/ryanhalphide/aibr-free-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/ryanhalphide/aibr-free-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-60-green)](skills/)
[![Agents](https://img.shields.io/badge/agents-12-orange)](agents/)
[![Hooks](https://img.shields.io/badge/hooks-18-purple)](hooks/)

**An open-source AI engineering platform for Claude Code — built from 12 months of production use.**

60 skills · 12 specialist agents · 18 lifecycle hooks · 7 architectural patterns · 1 MCP server · 1 Python orchestrator

[Install in 30 seconds](#installation) · [Browse Skills](#skills) · [Agent Hierarchy](#agents) · [Hook System](#hooks) · [GSD Framework](#gsd-framework) · [MCP Servers](#mcp-servers) · [Orchestrator](#python-orchestrator) · [Contributing](#contributing)

---

## What This Is

This is a complete Claude Code automation ecosystem — not a collection of prompt files. Skills orchestrate agents. Agents have specialized roles with explicit tool allowlists. Hooks create a self-healing runtime that catches errors before they become problems. Patterns document the design decisions that make the whole system coherent.

Most Claude Code setups are a flat folder of markdown commands. This framework treats Claude Code as a runtime environment with distinct layers: commands that delegate to specialized sub-agents, lifecycle hooks that enforce guardrails automatically, and an architectural pattern library that documents *why* the system is built the way it is. The result is a Claude Code setup that behaves consistently across projects and scales to complex multi-agent workflows.

Everything here was extracted from real production work — debugging voice agents, building data pipelines, shipping full-stack applications, managing multi-repo client engagements. Nothing was designed in the abstract. If a pattern is in this repo, it earned its place by solving a real problem that cost real time to discover.

---

## Architecture

```
                        ┌─────────────────────────────────┐
                        │           User Input             │
                        │    /skill command or free text   │
                        └─────────────────┬───────────────┘
                                          │
                        ┌─────────────────▼───────────────┐
                        │             Skills               │
                        │  /commands — 60 skill files      │
                        │  Orchestrate work, set context,  │
                        │  dispatch to specialist agents   │
                        └──────┬──────────────────┬───────┘
                               │                  │
               ┌───────────────▼──┐  ┌────────────▼──────────────┐
               │     Agents       │  │          Hooks             │
               │  12 specialist   │  │   18 lifecycle scripts     │
               │  roles, each     │  │   PreToolUse, PostToolUse  │
               │  scoped to a     │  │   Stop, SessionStart       │
               │  tool allowlist  │  │   Self-healing runtime     │
               └───────────────┬──┘  └────────────┬──────────────┘
                               │                  │
                        ┌──────▼──────────────────▼──────┐
                        │            Patterns             │
                        │   7 documented architecture     │
                        │   decisions — the "why"         │
                        │   behind every design choice    │
                        └─────────────────────────────────┘

  Skill categories:     Agent model tiers:      Hook events:
  ─────────────────     ────────────────────    ────────────────
  Debugging     (4)     Opus   → planning,      PreToolUse
  Git           (2)             security,        PostToolUse
  Code Quality  (2)             arch decisions   Stop
  Planning      (2)     ─────────────────────   SessionStart
  Productivity  (4)     Sonnet → code changes,
  Multi-Agent   (3)             implementation,  Additional layers:
  Knowledge     (4)             API work         ─────────────────
  Research      (2)     ─────────────────────   MCP Servers  (1)
  Video         (2)     Haiku  → search,        Python Daemon(1)
  Deployment    (3)             diagnostics,     Configs      (10)
  Social        (2)             lightweight reads Plugins     (1)
  GSD          (22)
  Vault/KM      (4)
  Career        (2)
```

The flow is intentional: skills are the interface, agents are the workers, hooks are the safety net, patterns are the documentation. Each layer has a single responsibility. No agent modifies `.env` files. No hook blocks valid work. Every skill declares its scope upfront.

---

## Installation

**One-liner:**
```bash
curl -fsSL https://raw.githubusercontent.com/ryanhalphide/aibr-free-skills/main/bootstrap.sh | bash
```

**Or clone manually:**
```bash
git clone https://github.com/ryanhalphide/aibr-free-skills.git
cd aibr-free-skills
chmod +x install.sh && ./install.sh
```

The installer symlinks skills into `~/.claude/commands/` and agents into `~/.claude/agents/`. Hooks are not auto-wired — the installer prints the exact JSON snippets to paste into your `settings.json`. This is intentional: hooks fire on every matching tool call, so you should consciously opt in to each one.

**Requirements:** Claude Code must be installed and `~/.claude/` must exist.

**Options:**
```bash
./install.sh --dry-run   # Preview what would be installed without making changes
./install.sh --force     # Overwrite existing symlinks
```

---

## Skills

Skills are invoked as `/skill-name` slash commands in Claude Code. Each skill file defines its scope, the tools it may use, and a step-by-step process. Complex skills delegate to specialist agents automatically — you get the result without managing the handoff.

### Debugging

| Skill | Description |
|---|---|
| `/quick-debug` | Hypothesis-first bug triage — reads error, checks git log, generates 3 ranked root causes, verifies the top one, applies a targeted fix |
| `/frustrated` | Resets context when stuck — lists attempts so far, forces a completely different approach |
| `/fix-tests` | Diagnoses failing tests without shotgun patching — identifies the specific breaking change and proposes a minimal fix |
| `/auto-debug` | Full autonomous debug loop — hypothesize, design cheapest test, confirm, fix, post-mortem |

### Git

| Skill | Description |
|---|---|
| `/smart-commit` | Generates semantic commit messages from the actual diff, stages intelligently, handles pre-commit hook failures without losing work |
| `/pr` | Creates a full PR with title, summary, test plan, and appropriate labels |

### Code Quality

| Skill | Description |
|---|---|
| `/project-scanner` | Five-point health audit — env vars, dependency health, security vulnerabilities, dead code, code quality signals. Scored report, nothing auto-fixed |
| `/fix-ci` | Diagnoses CI failures from raw logs, proposes a targeted fix without touching unrelated code |

### Planning

| Skill | Description |
|---|---|
| `/discovery` | Read-only project exploration — builds a complete mental model of the codebase before any writes happen |
| `/scaffold-claude-md` | Generates a project-specific CLAUDE.md from codebase analysis — stack detection, conventions, gotchas |

### Productivity

| Skill | Description |
|---|---|
| `/go` | Session starter — loads active context, resumes in-progress work, morning briefing mode |
| `/next` | Surfaces the single highest-priority next action from all open tasks |
| `/outstanding` | Full picture of in-progress work, blocked items, and pending decisions |
| `/preflight` | Pre-work checklist — confirms correct branch, env vars set, tests passing, dependencies installed |

### Multi-Agent

| Skill | Description |
|---|---|
| `/swarm` | Spawns N parallel agents for independent subtasks, collects and reconciles results |
| `/sprint` | Sequential specialist pipeline — explore then build then verify then deploy, each phase handoff explicit |
| `/hive` | Multi-terminal swarm coordination via file-based state — no network required (see Hive Coordination pattern) |

### Knowledge

| Skill | Description |
|---|---|
| `/graphify` | Converts any input (docs, transcripts, meeting notes, URLs) into a structured knowledge graph |
| `/wiki-ingest` | Ingests a URL or file into the project wiki with auto-tagging |
| `/wiki-query` | Answers questions from the project wiki with citations, not hallucinations |
| `/wiki-lint` | Audits the wiki for stale entries, broken links, and missing context |

### Research

| Skill | Description |
|---|---|
| `/auto-research` | Autonomous optimization loop — mutate, experiment, measure, keep or discard. Adapted from Karpathy's autoresearch pattern (see CREDITS.md) |
| `/creative-edge` | Generates unconventional approaches by systematically breaking constraints and inverting assumptions |

### Video

| Skill | Description |
|---|---|
| `/remotion` | Scaffolds and iterates Remotion video components with composition structure and timing |
| `/video-iterate` | Applies feedback to a rendered video — frame-accurate editing loop with visual diff |

### Deployment

| Skill | Description |
|---|---|
| `/deploy` | Runs deployment with pre-flight checks, branch verification, and env confirmation before any push |
| `/deploy-verify` | Post-deploy health check — probes live endpoints, checks logs, confirms the right version is live |
| `/system-health` | Full system status report — services, queues, scheduled jobs, recent errors, disk and memory |

### Social

| Skill | Description |
|---|---|
| `/social-draft` | Drafts platform-specific social content (LinkedIn, X, Instagram) from a brief |
| `/social-campaign` | Builds a multi-post campaign with scheduling, variant copy, and cross-platform adaptation |

### GSD Framework (22 commands)

A complete AI project management system. Manages multi-phase projects with milestones, assumption tracking, progress reporting, and automated work sequencing. Built from managing 6+ concurrent production projects.

| Skill | Description |
|---|---|
| `/new-project` | Scaffold a new project with phases, milestones, and success criteria |
| `/new-milestone` | Add a milestone with acceptance criteria and dependencies |
| `/create-roadmap` | Generate a visual project roadmap from current state |
| `/plan-phase` | Deep-plan a single phase with tasks, estimates, and risk flags |
| `/execute-plan` | Begin executing the current phase plan, tracking progress per-task |
| `/add-phase` / `/insert-phase` / `/remove-phase` | Modify the phase structure without losing progress |
| `/research-phase` | Research-only pass on a phase before committing to implementation |
| `/discuss-phase` / `/discuss-milestone` | Structured discussion with tradeoff analysis before decisions |
| `/consider-issues` | Surface blockers, risks, and open questions across all active phases |
| `/list-phase-assumptions` | Enumerate and rank unverified assumptions for the current phase |
| `/progress` | Current status across all phases and milestones with completion % |
| `/complete-milestone` | Mark a milestone done with evidence and update downstream dependencies |
| `/verify-work` | Run verification checks against milestone acceptance criteria |
| `/plan-fix` | Diagnose and plan a fix for a failing milestone or phase |
| `/map-codebase` | Generate an architectural map of the project codebase |
| `/pause-work` / `/resume-work` / `/resume-task` | Session lifecycle — save state, resume later, pick up a specific task |
| `/help` | GSD command reference and usage guide |

### Knowledge Management

A 4-skill vault system for building persistent, AI-assisted knowledge bases using the PARA method. Works with Obsidian or any markdown-based note system.

| Skill | Description |
|---|---|
| `/vault-capture` | Capture a new knowledge entry with auto-classification (Project/Area/Resource/Archive) |
| `/vault-sync` | Reconcile vault state — find orphans, fix broken links, update indexes |
| `/vault-review` | Audit vault health — stale entries, missing context, coverage gaps |
| `/vault-inbox` | Process the inbox — triage, classify, and route unprocessed captures |

### Career

| Skill | Description |
|---|---|
| `/resume-factory` | Generate role-targeted resume variants from a master profile with scoring |
| `/resume-iterate` | Iterative resume refinement based on job posting analysis and ATS optimization |

---

## GSD Framework

The GSD (Get Shit Done) framework is a 22-command project management system designed specifically for AI-assisted development. It solves the fundamental problem of Claude Code sessions: excellent at executing individual tasks, but no built-in scaffolding for tracking state, sequencing work, or maintaining context across sessions.

GSD provides that scaffolding. Projects have phases. Phases have milestones. Milestones have acceptance criteria. Progress is tracked automatically. Assumptions are logged and ranked. When you come back to a project after a week, `/progress` tells you exactly where you left off and `/resume-work` picks up the next task.

All 22 commands live in `skills/gsd/`. See `skills/gsd/README.md` for the full command reference.

---

## MCP Servers

### Session Sync (`mcp-servers/session-sync/`)

A TypeScript MCP server that enables real-time coordination between multiple Claude Code sessions. When you run 3+ terminals on the same project (common during `/hive` or `/sprint` workflows), sessions can broadcast events, detect file conflicts, and coordinate task assignment — all through the MCP protocol.

**12 MCP tools** including session registration, broadcast, event log queries, conflict detection, and stale session cleanup. Auto-registers using `process.ppid`. File-based state in `~/.claude/shared-state/` — no external server required.

Built with the official `@modelcontextprotocol/sdk` and compiles clean with zero TypeScript errors.

See `mcp-servers/session-sync/README.md` for architecture details and installation.

---

## Python Orchestrator

A 7-file async Python daemon (`orchestrator/`) that adds a persistent automation layer on top of Claude Code. Runs in the background monitoring your workspace:

| File | Purpose |
|---|---|
| `master-orchestrator.py` | Main daemon — watches directory changes, auto-executes skills, detects behavioral patterns |
| `model-router.py` | Keyword + context analysis for Opus/Sonnet/Haiku routing with cost logging |
| `session_manager.py` | Session lifecycle management |
| `progress-tracker.py` | Plan progress tracking across phases and milestones |
| `token-tracker.py` | Token usage tracking and budget enforcement |
| `activity-logger.py` | Structured activity logging for post-session analysis |
| `gsd-ralph-detector.py` | Detects "Ralph Wiggum loops" — repetitive stuck patterns that waste tokens |

All 7 files pass `py_compile` cleanly. See `orchestrator/README.md` for setup and background process configuration.

---

## Agents

The framework uses a 12-role agent hierarchy. Each agent has a defined scope, an explicit tool allowlist, and a model tier assignment. Specialization is the point — narrow scope produces more reliable output than general-purpose agents.

| Agent | Role | Model Tier |
|---|---|---|
| `planner` | Writes saved-plan.md for complex multi-phase tasks, aligns on approach before execution | Opus |
| `security-reviewer` | Audits code for vulnerabilities, auth gaps, injection risks, exposed secrets | Opus |
| `rh-reviewer` | Full code review with tradeoffs, alternatives, and explicit severity ratings | Opus |
| `feature-dev` | Full feature implementation across multiple files with cross-file import updates | Sonnet |
| `builder` | Targeted 1-2 file edits, minimal-footprint implementation | Sonnet |
| `verifier` | Runs tests, typechecks, build verification — reports pass/fail with evidence | Sonnet |
| `deployer` | Deployment execution and post-deploy confirmation, never touches source code | Sonnet |
| `plugin-dev` | Claude Code plugin and skill development, knows the skill spec format | Sonnet |
| `code-reviewer` | Targeted review of a specific diff or file, fast turnaround | Sonnet |
| `rh-explorer` | Read-only codebase investigation — no writes, no side effects, pure analysis | Haiku |
| `researcher` | Web research, documentation lookup, and synthesis across sources | Haiku |
| `diagnostics` | Log tailing, health checks, grep and search tasks — speed over depth | Haiku |

**Model routing rationale:** Opus for decisions that are expensive to reverse (architecture, security reviews, complex planning). Sonnet for implementation work. Haiku for read-only and diagnostic work where speed matters more than depth. This is the Model Routing pattern — documented in detail in `/patterns/model-routing.md`.

---

## Hooks

Hooks are shell scripts wired into Claude Code's lifecycle events. They fire automatically on every matching tool call — no skill invocation required. The hook system turns Claude Code from a reactive tool into a proactive one that catches problems before they land in the conversation.

**How to wire hooks:** The installer prints the exact JSON snippets to paste into `~/.claude/settings.json`. See `hooks/README.md` for full instructions and the complete hook reference.

### Hook Events

| Event | When It Fires | Use Cases |
|---|---|---|
| `PreToolUse` | Before any tool call — can block or warn | Branch protection, secret scanning, disk space checks |
| `PostToolUse` | After any tool call — can log or trigger side effects | Error diagnosis, test triggering, deploy verification |
| `Stop` | When Claude finishes a response | Memory extraction, session logging |
| `SessionStart` | At the start of a new session | Context loading, trust score initialization, vault sync |

### All 18 Hooks

| Hook | Event | Purpose |
|---|---|---|
| `session-awareness.sh` | SessionStart | Detects other active sessions, prevents conflicts |
| `janitor.sh` | SessionStart | TTL-based workspace cleanup |
| `inject-git-state.sh` | SessionStart | Auto-injects current git branch, status, recent commits |
| `vault-sync-auto.sh` | SessionStart | Syncs vault memory files at session start |
| `memory-reconcile.sh` | SessionStart | Reconciles memory index with actual memory files |
| `vault-structure-audit.sh` | SessionStart | Validates PARA directory structure |
| `trust-gate.sh` | PreToolUse | Progressive autonomy gate (see below) |
| `env-blocker.sh` | PreToolUse | Blocks writes to .env and credential files |
| `git-safety-check.sh` | PreToolUse | Pre-flight check on destructive git operations |
| `pre-deploy-check.sh` | PreToolUse | Validates deployment prerequisites before push |
| `auto-diagnose.sh` | PostToolUse | Self-healing error categorizer (see below) |
| `context-budget-warn.sh` | PostToolUse | Warns when approaching token/tool-call budget |
| `post-deploy-healthcheck.sh` | PostToolUse | Auto-probes health endpoints after deploy commands |
| `post-edit-typecheck.sh` | PostToolUse | Runs TypeScript compiler after file edits |
| `sync-emit.sh` | PostToolUse | Emits events to session-sync MCP for multi-session coordination |
| `memory-extract.sh` | Stop | AI-powered session insight extraction (see below) |
| `completeness-checker.md` | Stop | Validates all tasks are done before session ends |

### The 3 Most Novel Hooks

**auto-diagnose** (`hooks/post-tool/auto-diagnose.sh`)

A self-healing error categorizer. After any Bash tool call that exits non-zero, it reads the error output and matches it against 25+ failure mode signatures — auth errors, missing dependencies, build failures, network issues, permission errors, rate limits, and more. A structured diagnosis is injected into the next context window. Claude sees a categorized error type with a suggested first step, not just raw stderr. This eliminates the "retry the same command" loop that burns time in every debugging session.

**trust-gate** (`hooks/pre-tool/trust-gate.sh`)

Progressive autonomy based on a session-scoped trust score. New sessions start at a cautious level — destructive operations (force-push, DROP TABLE, rm -rf, production deploys) require explicit user confirmation. As the session progresses and the user approves actions, the trust score rises and confirmation prompts become less frequent. The score is persisted per-project in `~/.claude/cache/`. Think of it as a dial between "confirm everything" and "maximum initiative" that you earn during a session.

**memory-extract** (`hooks/stop/memory-extract.sh`)

AI-powered session distillation via the Claude Haiku API. When Claude finishes a response (Stop event), this hook sends the last N tool calls and outputs to Haiku with a structured extraction prompt. Haiku identifies decisions, surprises, and non-obvious learnings worth preserving across sessions, then writes them to the memory pipeline. The result: sessions self-document. You get persistent memory without manually running a `/session-end` command.

---

## Patterns

Seven architectural patterns are documented in `/patterns/`. Each is a standalone document explaining a design decision: the problem it solves, how it works, the tradeoffs, and when to use it.

| Pattern | Description |
|---|---|
| **Trust Gate** | Progressive AI autonomy via a session-scoped trust score. Blocks destructive ops at low trust, reduces friction as trust is earned through the session. |
| **Auto-Diagnose** | Self-healing error categorization with 25+ failure mode signatures. Structured diagnosis injected into context eliminates retry loops. |
| **Hive Coordination** | File-based multi-terminal swarm. Multiple Claude Code sessions coordinate via a shared state directory — no network, no server required. |
| **Agent Specialization** | The 12-role hierarchy design: why narrow scope outperforms generalists, how to assign tool allowlists, model tier selection criteria. |
| **Memory Pipeline** | How sessions produce persistent memory: Stop hook fires, Haiku extracts, memory file is written, MEMORY.md index is updated, next session loads it. |
| **Model Routing** | Cost-aware intelligent model selection. Decision tree for routing tasks to Opus, Sonnet, or Haiku based on reversibility, complexity, and time sensitivity. |
| **Hook Lifecycle** | The complete event-driven Claude Code runtime. How PreToolUse, PostToolUse, Stop, and SessionStart compose into a coherent safety and automation layer. |

---

## Configs

Example configurations in `configs/` that you can adapt:

- **`settings-example.jsonc`** — Fully annotated `settings.json` showing hook wiring, model routing, permissions, and MCP server configuration
- **Hookify templates** — 5 ready-to-use declarative hook rules (branch protection, secret scanning, disk space guard, retry limits, TypeScript lint)
- **Coding rules** — 4 rule files for production safety, TypeScript conventions, Python conventions, and workflow preferences

## Plugins

The `plugins/` directory contains example Claude Code plugins:

- **Optimizer** — A workspace audit plugin with two skills: `/optimize` (configuration + coverage gap analysis, scored report) and `/cost-track` (token cost estimation across sessions with reduction recommendations)

---

## Examples

See `examples/CLAUDE.md` for a worked reference showing how all the framework pieces wire together in a real TypeScript/Hono project — model routing, hook configuration, agent delegation rules, GSD integration, and memory system setup.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to add skills, agents, and hooks.

The short version: fork, create a branch, add your skill/agent/hook with correct frontmatter, verify `./install.sh --dry-run` works, submit a PR.

---

## About AIBR

AI Boost Realization builds production AI tooling for developers and teams.

- Website: [aibr.pro](https://aibr.pro)
- GitHub: [github.com/ryanhalphide](https://github.com/ryanhalphide)
- Agent Empire: [agentbuilder.aibr.pro](https://agentbuilder.aibr.pro)
- Agent Academy: [agents.aibr.pro](https://agents.aibr.pro)

---

## License

MIT — free to use, share, and fork. Attribution appreciated.

See [CREDITS.md](./CREDITS.md) for third-party attributions.
