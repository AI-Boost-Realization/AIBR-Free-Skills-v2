# session-sync MCP Server

A TypeScript MCP server that enables real-time coordination between multiple Claude Code terminals running simultaneously. It solves a fundamental limitation of Claude Code: the built-in Agent tool works within a single session, but when you have two or three terminals open on different projects, they have no awareness of each other.

This is running infrastructure, not a prompt file.

## What it does

When you run Claude Code in multiple terminals at the same time, session-sync lets each instance:

- See what every other terminal is currently working on
- Broadcast messages between sessions
- Claim files to prevent simultaneous edits
- Share a cross-session event log (task started, task completed, lesson learned, etc.)
- Detect drift since last check via a sync digest

The session store is a flat-file system in `~/.claude/shared-state/` — no database required. Each session writes a heartbeat file, and stale sessions (no heartbeat in 30 minutes, or dead process) are cleaned up automatically.

## Architecture

```
~/.claude/shared-state/
  sessions/
    term-12345.json    # one file per active terminal
    term-67890.json
  broadcasts.json      # ring buffer of last 50 messages
  event-log.jsonl      # append-only event log, rotates at 500KB
```

**SessionStore** (`session-store.ts`) handles all filesystem I/O. It uses atomic writes (write to `.tmp`, then rename) to prevent partial reads when two processes write simultaneously.

**index.ts** wires up the MCP tools and auto-registers the current session on startup using `process.ppid` as the terminal ID. Session identity survives reconnects as long as the parent terminal PID stays the same.

**Types** (`types.ts`) define `SessionInfo`, `BroadcastMessage`, and `SyncEvent` — all strict TypeScript interfaces, no loose objects.

## Tools

| Tool | Description |
|------|-------------|
| `register_session` | Register or update this session in the shared registry |
| `get_active_sessions` | List all active Claude Code sessions across terminals |
| `update_task` | Update what this session is working on |
| `broadcast_message` | Send a message visible to all other sessions |
| `check_file_conflicts` | Check if files you want to edit are claimed by another session |
| `claim_files` | Declare ownership of files to prevent concurrent edits |
| `deregister_session` | Remove this session on exit |
| `emit_event` | Emit a typed event to the cross-session log |
| `get_events` | Read events with filters (type, project, sequence, time) |
| `get_shared_tasks` | Cross-session task board (last 24h) |
| `sync_digest` | Summary of all other-session activity since your last check |
| `get_broadcasts` | Read recent broadcast messages |

## Installation

```bash
cd mcp-servers/session-sync
npm install
npm run build
```

Then add to your `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "session-sync": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-servers/session-sync/dist/index.js"]
    }
  }
}
```

## Customizing project detection

The `deriveProject()` function in `index.ts` maps directory name fragments to human-readable project names. Edit the `map` object to match your own project layout:

```typescript
const map: Record<string, string> = {
  "my-api": "API Server",
  "my-dashboard": "Dashboard",
  "my-ml-pipeline": "ML Pipeline",
};
```

If no key matches, it falls back to the directory basename.

## Usage patterns

**Start of session** — Claude auto-registers on startup. Optionally call `register_session` with a descriptive `task_summary`.

**During work** — Call `update_task` when switching tasks. Call `claim_files` before editing shared config files. Call `check_file_conflicts` before touching files another session might own.

**Cross-session coordination** — Use `broadcast_message` to signal when you've finished something another session is waiting on. Use `emit_event` with structured types (`task.complete`, `deploy.done`, `schema.changed`) for machine-readable coordination.

**Catching up** — Call `sync_digest` at the start of a new sub-task to see what other sessions did while you were focused elsewhere.

## Why file-based instead of a real IPC mechanism

Named pipes, Unix sockets, and shared memory all require a long-running coordinator process. With file-based state, each MCP server instance is independent — if one terminal crashes, the others keep working. The atomic rename pattern prevents torn reads. For the latency involved in AI-assisted development (seconds, not milliseconds), filesystem IPC is more than fast enough.
