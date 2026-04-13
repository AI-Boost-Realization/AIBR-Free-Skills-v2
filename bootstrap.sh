#!/usr/bin/env bash
# AIBR Agent Framework — One-line installer
# Usage: curl -fsSL https://raw.githubusercontent.com/ryanhalphide/aibr-free-skills/main/bootstrap.sh | bash
#
# This script clones the repo and runs the installer.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

INSTALL_DIR="${AIBR_INSTALL_DIR:-$HOME/.aibr-agent-framework}"

# Check prerequisites
if ! command -v git &>/dev/null; then
  echo -e "${RED}ERROR: git is required but not found.${RESET}"
  exit 1
fi

if [[ ! -d "$HOME/.claude" ]]; then
  echo -e "${RED}ERROR: ~/.claude/ not found. Install Claude Code first: https://claude.ai/code${RESET}"
  exit 1
fi

# Clone or update
if [[ -d "$INSTALL_DIR" ]]; then
  echo -e "${CYAN}Updating existing installation at $INSTALL_DIR${RESET}"
  cd "$INSTALL_DIR" && git pull --ff-only
else
  echo -e "${CYAN}Cloning AIBR Agent Framework...${RESET}"
  git clone https://github.com/ryanhalphide/aibr-free-skills.git "$INSTALL_DIR"
fi

# Run installer
cd "$INSTALL_DIR"
chmod +x install.sh
bash install.sh "$@"
