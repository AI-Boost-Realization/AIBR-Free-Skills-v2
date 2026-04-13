---
description: Pre-flight checklist before starting any task - catches missing auth and broken tools early
---

# Pre-Flight Checklist

Before starting any task, run through this checklist:

## Credentials & Auth
- Check if required API keys are set (look for .env files, environment variables)
- Verify MCP servers are configured in ~/.claude/mcp-servers.json
- Test auth for any external services needed (GitHub, Vercel, Linear, etc.)

## Environment
- Check git status and current branch
- Verify no uncommitted work that could conflict
- Check if dev servers are already running on needed ports
- Verify node_modules / dependencies are installed

## Scope
- Confirm the ONE deliverable for this session
- Create a TodoWrite checklist for the task
- Identify any blockers before starting

If any check fails, inform the user immediately with the specific issue and how to fix it. Do NOT proceed past a blocker hoping it won't matter.
