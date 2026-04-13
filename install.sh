#!/usr/bin/env bash
# AIBR Agent Framework — Installer
# Symlinks skills and agents into ~/.claude/. Hooks require manual wiring (see below).

set -euo pipefail

# ─── ANSI Colors ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ─── Flags ────────────────────────────────────────────────────────────────────
DRY_RUN=false
FORCE=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --force)   FORCE=true ;;
    --help|-h)
      echo "Usage: ./install.sh [--dry-run] [--force]"
      echo ""
      echo "  --dry-run   Preview what would be installed without making changes"
      echo "  --force     Overwrite existing symlinks"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown flag: $arg${RESET}"
      echo "Run ./install.sh --help for usage."
      exit 1
      ;;
  esac
done

# ─── Banner ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════╗${RESET}"
echo -e "${CYAN}${BOLD}║        AIBR Agent Framework — Installer          ║${RESET}"
echo -e "${CYAN}${BOLD}║           aibr.pro · github.com/aibr             ║${RESET}"
echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════╝${RESET}"
echo ""

if $DRY_RUN; then
  echo -e "${YELLOW}[DRY RUN] No changes will be made.${RESET}"
  echo ""
fi

# ─── Locate repo root ─────────────────────────────────────────────────────────
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"
AGENTS_DIR="$CLAUDE_DIR/agents"

# ─── Prerequisite check ───────────────────────────────────────────────────────
if [[ ! -d "$CLAUDE_DIR" ]]; then
  echo -e "${RED}ERROR: ~/.claude/ directory not found.${RESET}"
  echo ""
  echo "Claude Code must be installed before running this installer."
  echo "Install Claude Code: https://claude.ai/code"
  echo ""
  exit 1
fi

echo -e "${GREEN}Found ~/.claude/ — Claude Code is installed.${RESET}"
echo ""

# ─── Create target directories ────────────────────────────────────────────────
for dir in "$COMMANDS_DIR" "$AGENTS_DIR"; do
  if [[ ! -d "$dir" ]]; then
    if $DRY_RUN; then
      echo -e "${YELLOW}[dry-run] Would create: $dir${RESET}"
    else
      mkdir -p "$dir"
      echo -e "${GREEN}Created: $dir${RESET}"
    fi
  fi
done

# ─── Helper: symlink a file ───────────────────────────────────────────────────
SKILLS_INSTALLED=0
SKILLS_SKIPPED=0
AGENTS_INSTALLED=0
AGENTS_SKIPPED=0

symlink_file() {
  local src="$1"
  local dest="$2"
  local label="$3"  # "skill" or "agent"

  if [[ -L "$dest" ]] && ! $FORCE; then
    echo -e "  ${YELLOW}SKIP${RESET}  $(basename "$src") — symlink exists (use --force to overwrite)"
    if [[ "$label" == "skill" ]]; then ((SKILLS_SKIPPED++)); else ((AGENTS_SKIPPED++)); fi
    return
  fi

  if $DRY_RUN; then
    echo -e "  ${CYAN}[dry-run]${RESET} Would symlink: $(basename "$src") → $dest"
  else
    if [[ -L "$dest" ]]; then
      rm "$dest"
    fi
    ln -s "$src" "$dest"
    echo -e "  ${GREEN}LINK${RESET}  $(basename "$src")"
  fi

  if [[ "$label" == "skill" ]]; then ((SKILLS_INSTALLED++)); else ((AGENTS_INSTALLED++)); fi
}

# ─── Install Skills ───────────────────────────────────────────────────────────
SKILLS_DIR="$REPO_DIR/skills"

if [[ -d "$SKILLS_DIR" ]]; then
  echo -e "${BOLD}Installing skills → ~/.claude/commands/${RESET}"
  echo ""

  # Find all .md files in skills/ subdirectories, flatten into commands/
  # Skip README.md files — those are category docs, not skills
  while IFS= read -r -d '' skill_file; do
    filename="$(basename "$skill_file")"
    [[ "$filename" == "README.md" ]] && continue
    dest="$COMMANDS_DIR/$filename"
    symlink_file "$skill_file" "$dest" "skill"
  done < <(find "$SKILLS_DIR" -name "*.md" -print0 | sort -z)

  echo ""
else
  echo -e "${YELLOW}WARNING: skills/ directory not found at $SKILLS_DIR${RESET}"
fi

# ─── Install Agents ───────────────────────────────────────────────────────────
AGENTS_SRC_DIR="$REPO_DIR/agents"

if [[ -d "$AGENTS_SRC_DIR" ]]; then
  echo -e "${BOLD}Installing agents → ~/.claude/agents/${RESET}"
  echo ""

  while IFS= read -r -d '' agent_file; do
    filename="$(basename "$agent_file")"
    [[ "$filename" == "README.md" ]] && continue
    dest="$AGENTS_DIR/$filename"
    symlink_file "$agent_file" "$dest" "agent"
  done < <(find "$AGENTS_SRC_DIR" -name "*.md" -print0 | sort -z)

  echo ""
else
  echo -e "${YELLOW}WARNING: agents/ directory not found at $AGENTS_SRC_DIR${RESET}"
fi

# ─── MCP Server: Build Instructions ──────────────────────────────────────────
MCP_DIR="$REPO_DIR/mcp-servers/session-sync"

if [[ -d "$MCP_DIR" ]]; then
  echo -e "${BOLD}MCP Server — Session Sync${RESET}"
  echo ""
  echo -e "To install the session-sync MCP server:"
  echo -e "  ${CYAN}cd $MCP_DIR && npm install && npm run build${RESET}"
  echo ""
  echo -e "Then add to ${CYAN}~/.claude/settings.json${RESET} under ${CYAN}\"mcpServers\"${RESET}:"
  echo ""
  cat << MCPJSON
    "session-sync": {
      "command": "node",
      "args": ["$MCP_DIR/dist/index.js"]
    }
MCPJSON
  echo ""
fi

# ─── Python Orchestrator: Install Instructions ────────────────────────────────
ORCH_DIR="$REPO_DIR/orchestrator"

if [[ -d "$ORCH_DIR" ]]; then
  echo -e "${BOLD}Python Orchestrator${RESET}"
  echo ""
  echo -e "Requirements: Python 3.11+, watchdog, anthropic"
  echo -e "  ${CYAN}pip install watchdog anthropic${RESET}"
  echo -e "Run in background:"
  echo -e "  ${CYAN}nohup python $ORCH_DIR/master-orchestrator.py &${RESET}"
  echo ""
fi

# ─── Hooks: Manual Wiring Instructions ───────────────────────────────────────
echo -e "${BOLD}Hooks — Manual Wiring Required${RESET}"
echo ""
echo -e "Hooks are NOT auto-installed. They fire on every matching tool call,"
echo -e "so you should consciously opt in. Paste the relevant blocks into"
echo -e "${CYAN}~/.claude/settings.json${RESET} under the ${CYAN}\"hooks\"${RESET} key."
echo ""
echo -e "${YELLOW}Example hooks configuration for settings.json:${RESET}"
echo ""
cat << 'HOOKS_JSON'
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/pre-tool/trust-gate.sh"
          },
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/pre-tool/branch-protection.sh"
          },
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/pre-tool/secret-scanner.sh"
          },
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/pre-tool/disk-space-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/post-tool/auto-diagnose.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/stop/memory-extract.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/session-start/load-context.sh"
          }
        ]
      }
    ]
  }
HOOKS_JSON

echo ""
echo -e "Full hook documentation: ${CYAN}./hooks/README.md${RESET}"
echo ""

# ─── Configs ──────────────────────────────────────────────────────────────────
echo -e "${BOLD}Configs${RESET}"
echo ""
echo -e "See ${CYAN}./configs/${RESET} for example configurations:"
echo -e "  ${CYAN}./configs/settings-example.jsonc${RESET}  — Annotated settings.json template"
echo -e "  ${CYAN}./configs/rules/${RESET}                  — Copy rules files to ~/.claude/rules/"
echo -e "  ${CYAN}./configs/hookify-templates/${RESET}       — Hookify rule templates"
echo ""
echo -e "Copy what's useful — none of these are auto-installed."
echo ""

# ─── Summary ──────────────────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}─────────────────────────────────────────────────${RESET}"
if $DRY_RUN; then
  echo -e "${YELLOW}${BOLD}Dry run complete — no changes made.${RESET}"
else
  echo -e "${GREEN}${BOLD}Installation complete.${RESET}"
  echo ""
  echo -e "  Skills installed:  ${GREEN}${BOLD}${SKILLS_INSTALLED}${RESET}"
  echo -e "  Skills skipped:    ${YELLOW}${SKILLS_SKIPPED}${RESET} (already symlinked)"
  echo -e "  Agents installed:  ${GREEN}${BOLD}${AGENTS_INSTALLED}${RESET}"
  echo -e "  Agents skipped:    ${YELLOW}${AGENTS_SKIPPED}${RESET} (already symlinked)"
fi
echo ""
echo -e "Next steps:"
echo -e "  1. Wire hooks into settings.json (see instructions above)"
echo -e "  2. Copy any rules from ./configs/rules/ that fit your workflow"
echo -e "  3. Open a Claude Code session and try: ${CYAN}/quick-debug${RESET}"
echo ""
echo -e "${CYAN}See hooks/README.md to wire the lifecycle hooks.${RESET}"
echo ""
