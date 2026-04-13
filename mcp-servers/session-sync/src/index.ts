import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { SessionStore } from "./session-store.js";
import type { SessionInfo } from "./types.js";

const store = new SessionStore();
const MY_TERMINAL_ID = `term-${process.ppid}`;

// Auto-register this session on startup
const existingSession = store.get(MY_TERMINAL_ID);
if (!existingSession) {
  store.register({
    terminal_id: MY_TERMINAL_ID,
    pid: process.ppid,
    directory: process.cwd(),
    project: deriveProject(process.cwd()),
    started: new Date().toISOString(),
    heartbeat: new Date().toISOString(),
    status: "active",
    task_summary: "Starting session",
    tools_used: 0,
  });
}

function deriveProject(dir: string): string {
  // Map directory name fragments to human-readable project names.
  // Customize this map to match your own project directory layout.
  const map: Record<string, string> = {
    "my-trading-bot": "Trading Bot",
    "my-web-app": "Web App",
    "my-api": "API Server",
    "my-cli": "CLI Tool",
  };
  for (const [key, name] of Object.entries(map)) {
    if (dir.includes(key)) return name;
  }
  return dir.split("/").pop() || "unknown";
}

function formatSessions(sessions: SessionInfo[]): string {
  if (sessions.length === 0) return "No other active sessions.";
  return sessions
    .map((s, i) => {
      const age = Math.round(
        (Date.now() - new Date(s.heartbeat).getTime()) / 60000
      );
      const ageStr =
        age < 1 ? "just now" : age < 60 ? `${age}min ago` : `${Math.round(age / 60)}h ago`;
      const files = s.claimed_files?.length
        ? ` [${s.claimed_files.length} files claimed]`
        : "";
      return `  #${i + 1}  ${s.project} (${s.terminal_id}) — ${ageStr} — "${s.task_summary}"${files}`;
    })
    .join("\n");
}

const server = new McpServer({
  name: "session-sync",
  version: "1.0.0",
});

// --- Tools ---

server.tool(
  "register_session",
  "Register or update this Claude Code session in the shared registry",
  {
    directory: z.string().describe("Working directory of the session"),
    project: z.string().optional().describe("Project name (auto-detected if omitted)"),
    task_summary: z.string().optional().describe("What this session is working on"),
  },
  async ({ directory, project, task_summary }) => {
    store.register({
      terminal_id: MY_TERMINAL_ID,
      pid: process.ppid,
      directory,
      project: project || deriveProject(directory),
      started: existingSession?.started || new Date().toISOString(),
      heartbeat: new Date().toISOString(),
      status: "active",
      task_summary: task_summary || "Working",
      tools_used: existingSession?.tools_used || 0,
    });
    return {
      content: [
        {
          type: "text" as const,
          text: `Session ${MY_TERMINAL_ID} registered for ${project || deriveProject(directory)}.`,
        },
      ],
    };
  }
);

server.tool(
  "get_active_sessions",
  "List all active Claude Code sessions across all terminals",
  {
    include_self: z.boolean().optional().describe("Include this session in results (default: false)"),
  },
  async ({ include_self }) => {
    const sessions = store.getAll(include_self ? undefined : MY_TERMINAL_ID);
    const summary = formatSessions(sessions);
    return {
      content: [
        {
          type: "text" as const,
          text: `=== Active Claude Sessions (${sessions.length}) ===\n${summary}\n===============================`,
        },
      ],
    };
  }
);

server.tool(
  "update_task",
  "Update what this session is currently working on",
  {
    task_summary: z.string().describe("Short description of current task"),
    status: z.enum(["active", "idle", "busy"]).optional().describe("Session status"),
  },
  async ({ task_summary, status }) => {
    const s = store.get(MY_TERMINAL_ID);
    if (s) {
      s.task_summary = task_summary;
      if (status) s.status = status;
      s.heartbeat = new Date().toISOString();
      store.register(s);
    }
    return {
      content: [
        {
          type: "text" as const,
          text: `Task updated: "${task_summary}"`,
        },
      ],
    };
  }
);

server.tool(
  "broadcast_message",
  "Send a message visible to all other Claude Code sessions",
  {
    message: z.string().describe("Message to broadcast"),
  },
  async ({ message }) => {
    const s = store.get(MY_TERMINAL_ID);
    const from = s ? `${s.project} (${MY_TERMINAL_ID})` : MY_TERMINAL_ID;
    store.broadcast(from, message);
    store.emitEvent(MY_TERMINAL_ID, s?.project || "unknown", "broadcast", { from, message });
    const sessions = store.getAll(MY_TERMINAL_ID);
    return {
      content: [
        {
          type: "text" as const,
          text: `Broadcast sent to ${sessions.length} other session(s): "${message}"`,
        },
      ],
    };
  }
);

server.tool(
  "check_file_conflicts",
  "Check if files you want to edit are claimed by another session",
  {
    files: z.array(z.string()).describe("Absolute file paths to check"),
  },
  async ({ files }) => {
    const conflicts = store.checkFileConflicts(MY_TERMINAL_ID, files);
    if (conflicts.length === 0) {
      return {
        content: [
          {
            type: "text" as const,
            text: `No conflicts — ${files.length} file(s) are free to edit.`,
          },
        ],
      };
    }
    const lines = conflicts.map(
      (c) => `  CONFLICT: ${c.file} — claimed by ${c.owner.project} (${c.owner.terminal_id})`
    );
    return {
      content: [
        {
          type: "text" as const,
          text: `WARNING: ${conflicts.length} conflict(s) found:\n${lines.join("\n")}`,
        },
      ],
    };
  }
);

server.tool(
  "claim_files",
  "Declare ownership of files to prevent other sessions from editing them",
  {
    files: z.array(z.string()).describe("Absolute file paths to claim"),
  },
  async ({ files }) => {
    store.claimFiles(MY_TERMINAL_ID, files);
    const s = store.get(MY_TERMINAL_ID);
    store.emitEvent(MY_TERMINAL_ID, s?.project || "unknown", "file.claim", { files });
    return {
      content: [
        {
          type: "text" as const,
          text: `Claimed ${files.length} file(s) for ${MY_TERMINAL_ID}.`,
        },
      ],
    };
  }
);

server.tool(
  "deregister_session",
  "Remove this session from the registry (call on exit)",
  {},
  async () => {
    store.deregister(MY_TERMINAL_ID);
    return {
      content: [
        {
          type: "text" as const,
          text: `Session ${MY_TERMINAL_ID} deregistered.`,
        },
      ],
    };
  }
);

// ── Cross-Session Sync Tools ─────────────────────────────────────────────

server.tool(
  "emit_event",
  "Emit a sync event to the cross-session event log",
  {
    type: z.string().describe("Event type (e.g., 'task.create', 'lesson.learned')"),
    payload: z.record(z.string(), z.unknown()).describe("Event-specific payload"),
  },
  async ({ type, payload }) => {
    const s = store.get(MY_TERMINAL_ID);
    store.emitEvent(MY_TERMINAL_ID, s?.project || "unknown", type, payload);
    return { content: [{ type: "text" as const, text: `Event emitted: ${type}` }] };
  }
);

server.tool(
  "get_events",
  "Read sync events since a sequence number or timestamp, with optional filters",
  {
    since_seq: z.number().optional().describe("Read events after this sequence number"),
    since_time: z.string().optional().describe("ISO timestamp — read events after this time"),
    types: z.array(z.string()).optional().describe("Filter by event types"),
    project: z.string().optional().describe("Filter by project name"),
    limit: z.number().optional().describe("Max events to return (default: 50)"),
  },
  async ({ since_seq, since_time, types, project, limit }) => {
    const events = store.getEvents({
      since_seq, since_time, types, project,
      limit: limit || 50,
    });
    if (events.length > 0) {
      const session = store.get(MY_TERMINAL_ID);
      if (session) {
        session.event_cursor = events[events.length - 1].seq;
        store.register(session);
      }
    }
    if (events.length === 0) {
      return { content: [{ type: "text" as const, text: "No events found." }] };
    }
    const lines = events.map(e =>
      `[${e.ts}] ${e.sid}/${e.project}: ${e.type} — ${JSON.stringify(e.payload)}`
    );
    return { content: [{ type: "text" as const, text: `Events (${events.length}):\n${lines.join("\n")}` }] };
  }
);

server.tool(
  "get_shared_tasks",
  "View task events across all active sessions — cross-session task board",
  {
    project: z.string().optional().describe("Filter by project name"),
  },
  async ({ project }) => {
    const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    const events = store.getEvents({
      since_time: since,
      types: ["task.create", "task.complete", "task.update"],
      project,
      limit: 200,
    });
    if (events.length === 0) {
      return { content: [{ type: "text" as const, text: "No task events in the last 24 hours." }] };
    }
    const tasks = new Map<string, { title: string; status: string; session: string; project: string; ts: string }>();
    for (const e of events) {
      const title = (e.payload.title as string) || "untitled";
      const key = `${e.sid}:${title}`;
      if (e.type === "task.create") {
        tasks.set(key, { title, status: "in_progress", session: e.sid, project: e.project, ts: e.ts });
      } else if (e.type === "task.complete") {
        tasks.set(key, { title, status: "completed", session: e.sid, project: e.project, ts: e.ts });
      }
    }
    const lines = Array.from(tasks.values()).map(t =>
      `  [${t.status === "completed" ? "done" : "active"}] ${t.project}/${t.session}: ${t.title}`
    );
    return { content: [{ type: "text" as const, text: `Cross-Session Tasks (24h):\n${lines.join("\n")}` }] };
  }
);

server.tool(
  "sync_digest",
  "Get a human-readable summary of cross-session activity since your last check",
  {},
  async () => {
    const session = store.get(MY_TERMINAL_ID);
    const cursor = session?.event_cursor || 0;
    const events = store.getEvents({
      since_seq: cursor,
      excludeSid: MY_TERMINAL_ID,
      limit: 200,
    });
    if (events.length > 0 && session) {
      session.event_cursor = events[events.length - 1].seq;
      store.register(session);
    }
    if (events.length === 0) {
      return { content: [{ type: "text" as const, text: "No activity from other sessions since last check." }] };
    }
    const groups = new Map<string, typeof events>();
    for (const e of events) {
      const arr = groups.get(e.type) || [];
      arr.push(e);
      groups.set(e.type, arr);
    }
    const lines: string[] = [];
    for (const [type, evts] of groups) {
      const examples = evts.slice(-3).map(e => {
        const detail = e.payload.message || e.payload.path || e.payload.title || JSON.stringify(e.payload);
        return `    ${e.sid}/${e.project}: ${detail}`;
      });
      lines.push(`  ${type} (${evts.length}):`);
      lines.push(...examples);
    }
    return {
      content: [{
        type: "text" as const,
        text: `=== Sync Digest (${events.length} events) ===\n${lines.join("\n")}\n===============================`,
      }],
    };
  }
);

server.tool(
  "get_broadcasts",
  "Read recent broadcast messages from other sessions",
  {
    since: z.string().optional().describe("ISO timestamp — only show messages after this time"),
  },
  async ({ since }) => {
    const msgs = store.getRecentBroadcasts(since);
    if (msgs.length === 0) {
      return {
        content: [{ type: "text" as const, text: "No recent broadcasts." }],
      };
    }
    const lines = msgs.map((m) => `  [${m.timestamp}] ${m.from}: ${m.message}`);
    return {
      content: [
        {
          type: "text" as const,
          text: `Recent broadcasts (${msgs.length}):\n${lines.join("\n")}`,
        },
      ],
    };
  }
);

// --- Cleanup on exit ---
process.on("SIGTERM", () => {
  store.deregister(MY_TERMINAL_ID);
  process.exit(0);
});
process.on("SIGINT", () => {
  store.deregister(MY_TERMINAL_ID);
  process.exit(0);
});

// --- Start server ---
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("session-sync MCP server failed:", err);
  process.exit(1);
});
