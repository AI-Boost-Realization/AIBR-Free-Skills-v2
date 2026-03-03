# AIBR Free Skills for Claude Code

Production-ready skills for Claude Code. Built by [AIBR](https://aibr-hub.vercel.app) — extracted from real consulting workflows.

## Skills

| Skill | What it does |
|-------|-------------|
| [quick-debug](./skills/quick-debug.md) | Hypothesis-first debugging. Identifies 3 ranked root causes, verifies most likely first, prevents fix-loop rabbit holes. |
| [smart-commit](./skills/smart-commit.md) | Auto-stages relevant files, generates commit messages from diff analysis, handles pre-commit hooks gracefully. |
| [project-scanner](./skills/project-scanner.md) | Scans for missing env vars, outdated deps, security issues, and unused exports. Generates a health report. |

## Installation

```bash
# Clone into your Claude Code skills directory
git clone https://github.com/aiboosted4/aibr-free-skills.git
cp aibr-free-skills/skills/*.md ~/.claude/skills/
```

Or copy individual skill files directly into `~/.claude/skills/`.

## Usage

Once installed, Claude Code will automatically detect and use these skills when relevant:

- Start debugging any issue → `quick-debug` activates
- Run `/commit` or ask to commit → `smart-commit` activates
- Ask "scan this project" or "health check" → `project-scanner` activates

## Want More?

These 3 skills are a sample from the full AIBR toolkit:

| Product | Skills | Price |
|---------|--------|-------|
| [Claude Code Power User Framework](https://aiboosted4.gumroad.com/l/claude-code-power-user) | 50+ skills, plugin framework, orchestrator configs | $197 |
| [AI Agent Blueprint Kit](https://aiboosted4.gumroad.com/l/ai-agent-blueprint-kit) | 10 agent archetypes, model routing, hive coordination, memory system | $497 |
| [Revenue Cron Playbook](https://aiboosted4.gumroad.com/l/revenue-cron-playbook) | 19 cron job configs for lead hunting, content, and revenue alerts | $197 |
| [MCP Server Starter Packs](https://aiboosted4.gumroad.com/l/mcp-starter-packs) | 10+ pre-configured MCP server setups for Claude Code | $97 |

## Newsletter

Weekly Claude Code tips, agent framework tutorials, and automation deep-dives:

**[Subscribe to AIBR Weekly](https://aibr.beehiiv.com)**

## License

MIT — use freely in personal and commercial projects. Attribution appreciated but not required.

## Contributing

Found a bug? Have a skill idea? Open an issue or PR.

---

Built by [Ryan @ AIBR](https://aibr-hub.vercel.app) — AI consulting and agent frameworks for solo operators.
