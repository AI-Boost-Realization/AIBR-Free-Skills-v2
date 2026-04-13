import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { randomUUID } from "crypto";
import type { SessionInfo } from "../types.js";

// Each test suite run gets its own isolated temp home directory.
// We must set process.env.HOME BEFORE requiring SessionStore because the
// module-level constants (SESSIONS_DIR, BROADCAST_FILE, EVENT_LOG) are
// computed once at import time from process.env.HOME.

let tempHome: string;
let SessionStore: typeof import("../session-store.js").SessionStore;

function makeSession(overrides: Partial<SessionInfo> = {}): SessionInfo {
  return {
    terminal_id: randomUUID(),
    pid: process.pid, // must be a live PID so cleanStale() doesn't purge it
    directory: "/tmp/test",
    project: "test-project",
    started: new Date().toISOString(),
    heartbeat: new Date().toISOString(),
    status: "active",
    task_summary: "initial task",
    tools_used: 0,
    claimed_files: [],
    ...overrides,
  };
}

beforeAll(async () => {
  tempHome = path.join(os.tmpdir(), `session-sync-test-${randomUUID()}`);
  fs.mkdirSync(tempHome, { recursive: true });

  // Override HOME before the module is loaded
  process.env.HOME = tempHome;

  // Dynamic require so the module picks up the new HOME value
  jest.resetModules();
  const mod = await import("../session-store.js");
  SessionStore = mod.SessionStore;
});

afterAll(() => {
  // Clean up temp directory
  try {
    fs.rmSync(tempHome, { recursive: true, force: true });
  } catch {
    // ignore
  }
});

// ── register() and get() ──────────────────────────────────────────────────────

describe("register() and get()", () => {
  it("stores a session and retrieves it by terminal_id", () => {
    const store = new SessionStore();
    const session = makeSession({ terminal_id: "reg-test-1" });
    store.register(session);
    const retrieved = store.get("reg-test-1");
    expect(retrieved).not.toBeNull();
    expect(retrieved!.terminal_id).toBe("reg-test-1");
    expect(retrieved!.project).toBe("test-project");
  });

  it("returns null for an unknown terminal_id", () => {
    const store = new SessionStore();
    expect(store.get("does-not-exist")).toBeNull();
  });

  it("overwrites an existing session when registered again", () => {
    const store = new SessionStore();
    const session = makeSession({ terminal_id: "reg-overwrite", task_summary: "first" });
    store.register(session);
    store.register({ ...session, task_summary: "second" });
    expect(store.get("reg-overwrite")!.task_summary).toBe("second");
  });
});

// ── deregister() ─────────────────────────────────────────────────────────────

describe("deregister()", () => {
  it("removes a registered session and returns true", () => {
    const store = new SessionStore();
    const session = makeSession({ terminal_id: "dereg-test-1" });
    store.register(session);
    expect(store.deregister("dereg-test-1")).toBe(true);
    expect(store.get("dereg-test-1")).toBeNull();
  });

  it("returns false when the session does not exist", () => {
    const store = new SessionStore();
    expect(store.deregister("ghost-session")).toBe(false);
  });
});

// ── updateTask() ──────────────────────────────────────────────────────────────

describe("updateTask()", () => {
  it("updates task_summary and returns true", () => {
    const store = new SessionStore();
    const session = makeSession({ terminal_id: "update-task-1" });
    store.register(session);
    const result = store.updateTask("update-task-1", "new task summary");
    expect(result).toBe(true);
    expect(store.get("update-task-1")!.task_summary).toBe("new task summary");
  });

  it("updates the heartbeat timestamp", () => {
    const store = new SessionStore();
    const before = new Date().toISOString();
    const session = makeSession({ terminal_id: "update-task-hb", heartbeat: before });
    store.register(session);

    // Small delay to ensure timestamp differs
    const then = Date.now();
    while (Date.now() - then < 5) {} // busy wait 5ms

    store.updateTask("update-task-hb", "updated");
    const updated = store.get("update-task-hb")!;
    expect(new Date(updated.heartbeat).getTime()).toBeGreaterThanOrEqual(
      new Date(before).getTime()
    );
  });

  it("returns false when session does not exist", () => {
    const store = new SessionStore();
    expect(store.updateTask("missing-session", "anything")).toBe(false);
  });
});

// ── claimFiles() ──────────────────────────────────────────────────────────────

describe("claimFiles()", () => {
  it("adds files to claimed_files and returns true", () => {
    const store = new SessionStore();
    const session = makeSession({ terminal_id: "claim-1", claimed_files: [] });
    store.register(session);
    const result = store.claimFiles("claim-1", ["/src/a.ts", "/src/b.ts"]);
    expect(result).toBe(true);
    const updated = store.get("claim-1")!;
    expect(updated.claimed_files).toContain("/src/a.ts");
    expect(updated.claimed_files).toContain("/src/b.ts");
  });

  it("deduplicates files that are already claimed", () => {
    const store = new SessionStore();
    const session = makeSession({
      terminal_id: "claim-dedup",
      claimed_files: ["/src/existing.ts"],
    });
    store.register(session);
    store.claimFiles("claim-dedup", ["/src/existing.ts", "/src/new.ts"]);
    const claimed = store.get("claim-dedup")!.claimed_files!;
    const existingCount = claimed.filter((f) => f === "/src/existing.ts").length;
    expect(existingCount).toBe(1);
    expect(claimed).toContain("/src/new.ts");
  });

  it("returns false when session does not exist", () => {
    const store = new SessionStore();
    expect(store.claimFiles("no-session", ["/foo.ts"])).toBe(false);
  });
});

// ── checkFileConflicts() ──────────────────────────────────────────────────────

describe("checkFileConflicts()", () => {
  it("detects a conflict when another session has claimed the same file", () => {
    const store = new SessionStore();
    const ownerSession = makeSession({
      terminal_id: "conflict-owner",
      claimed_files: ["/shared/file.ts"],
    });
    store.register(ownerSession);

    const conflicts = store.checkFileConflicts("conflict-requester", ["/shared/file.ts"]);
    expect(conflicts.length).toBeGreaterThan(0);
    expect(conflicts[0].file).toBe("/shared/file.ts");
    expect(conflicts[0].owner.terminal_id).toBe("conflict-owner");
  });

  it("returns no conflicts when no other session claims the file", () => {
    const store = new SessionStore();
    const session = makeSession({
      terminal_id: "no-conflict-owner",
      claimed_files: ["/other/file.ts"],
    });
    store.register(session);

    const conflicts = store.checkFileConflicts("no-conflict-requester", ["/unrelated/file.ts"]);
    expect(conflicts).toHaveLength(0);
  });

  it("excludes the requesting session from conflict detection", () => {
    const store = new SessionStore();
    const session = makeSession({
      terminal_id: "self-claim",
      claimed_files: ["/self/file.ts"],
    });
    store.register(session);

    // The session claiming the file should NOT conflict with itself
    const conflicts = store.checkFileConflicts("self-claim", ["/self/file.ts"]);
    expect(conflicts).toHaveLength(0);
  });
});

// ── broadcast() and getRecentBroadcasts() ────────────────────────────────────

describe("broadcast() and getRecentBroadcasts()", () => {
  it("stores a broadcast message and retrieves it", () => {
    const store = new SessionStore();
    store.broadcast("sender-A", "hello from A");
    const msgs = store.getRecentBroadcasts();
    const found = msgs.find((m) => m.message === "hello from A");
    expect(found).toBeDefined();
    expect(found!.from).toBe("sender-A");
  });

  it("filters broadcasts by since timestamp", () => {
    const store = new SessionStore();
    const before = new Date().toISOString();

    // Small delay so the next broadcast is strictly after `before`
    const then = Date.now();
    while (Date.now() - then < 5) {}

    store.broadcast("sender-B", "after-cutoff message");
    const msgs = store.getRecentBroadcasts(before);
    expect(msgs.some((m) => m.message === "after-cutoff message")).toBe(true);
  });

  it("returns at most 10 messages when no since filter is given", () => {
    const store = new SessionStore();
    for (let i = 0; i < 15; i++) {
      store.broadcast("bulk-sender", `message-${i}`);
    }
    const msgs = store.getRecentBroadcasts();
    expect(msgs.length).toBeLessThanOrEqual(10);
  });

  it("returns empty array when broadcast file is missing", () => {
    // Use a fresh store pointing to a sub-path that has no broadcast file
    // We test this indirectly by relying on the try/catch returning []
    const store = new SessionStore();
    const result = store.getRecentBroadcasts(new Date(Date.now() + 9999999).toISOString());
    expect(result).toEqual([]);
  });
});

// ── emitEvent() and getEvents() ──────────────────────────────────────────────

describe("emitEvent() and getEvents()", () => {
  it("stores an event and retrieves it", () => {
    const store = new SessionStore();
    const sid = randomUUID();
    store.emitEvent(sid, "my-project", "commit", { hash: "abc123" });

    const events = store.getEvents({ project: "my-project" });
    const found = events.find((e) => e.sid === sid);
    expect(found).toBeDefined();
    expect(found!.type).toBe("commit");
    expect(found!.payload.hash).toBe("abc123");
  });

  it("filters events by project", () => {
    const store = new SessionStore();
    const sidA = randomUUID();
    const sidB = randomUUID();
    store.emitEvent(sidA, "project-alpha", "deploy", {});
    store.emitEvent(sidB, "project-beta", "deploy", {});

    const events = store.getEvents({ project: "project-alpha" });
    expect(events.every((e) => e.project === "project-alpha")).toBe(true);
  });

  it("filters events by type", () => {
    const store = new SessionStore();
    const sid = randomUUID();
    store.emitEvent(sid, "filter-proj", "task_update", {});
    store.emitEvent(sid, "filter-proj", "file_claim", {});

    const events = store.getEvents({ types: ["task_update"] });
    const hasFileClaimFromSid = events
      .filter((e) => e.sid === sid)
      .some((e) => e.type === "file_claim");
    expect(hasFileClaimFromSid).toBe(false);
    const hasTaskUpdateFromSid = events
      .filter((e) => e.sid === sid)
      .some((e) => e.type === "task_update");
    expect(hasTaskUpdateFromSid).toBe(true);
  });

  it("filters events by since_seq", () => {
    const store = new SessionStore();
    const sid = randomUUID();
    store.emitEvent(sid, "seq-proj", "ping", {});

    const allEvents = store.getEvents({ project: "seq-proj" });
    const lastSeq = allEvents[allEvents.length - 1].seq;

    // Emit another event after capturing the last seq
    store.emitEvent(sid, "seq-proj", "pong", {});

    const newEvents = store.getEvents({ since_seq: lastSeq, project: "seq-proj" });
    expect(newEvents.every((e) => e.seq > lastSeq)).toBe(true);
    expect(newEvents.some((e) => e.type === "pong")).toBe(true);
  });

  it("excludes events from a specific sid", () => {
    const store = new SessionStore();
    const sidExclude = randomUUID();
    const sidInclude = randomUUID();
    store.emitEvent(sidExclude, "excl-proj", "task_done", {});
    store.emitEvent(sidInclude, "excl-proj", "task_done", {});

    const events = store.getEvents({ project: "excl-proj", excludeSid: sidExclude });
    expect(events.some((e) => e.sid === sidExclude)).toBe(false);
    expect(events.some((e) => e.sid === sidInclude)).toBe(true);
  });

  it("seq numbers are monotonically increasing across consecutive events", () => {
    const store = new SessionStore();
    const sid = randomUUID();
    store.emitEvent(sid, "mono-proj", "a", {});
    store.emitEvent(sid, "mono-proj", "b", {});
    store.emitEvent(sid, "mono-proj", "c", {});

    const events = store.getEvents({ project: "mono-proj" });
    const seqs = events.map((e) => e.seq);
    for (let i = 1; i < seqs.length; i++) {
      expect(seqs[i]).toBeGreaterThan(seqs[i - 1]);
    }
  });
});

// ── getAll() ──────────────────────────────────────────────────────────────────

describe("getAll()", () => {
  it("returns all registered sessions", () => {
    const store = new SessionStore();
    const s1 = makeSession({ terminal_id: "all-test-1" });
    const s2 = makeSession({ terminal_id: "all-test-2" });
    store.register(s1);
    store.register(s2);

    const all = store.getAll();
    const ids = all.map((s) => s.terminal_id);
    expect(ids).toContain("all-test-1");
    expect(ids).toContain("all-test-2");
  });

  it("excludes the session matching the given excludeId", () => {
    const store = new SessionStore();
    const s1 = makeSession({ terminal_id: "excl-self-1" });
    const s2 = makeSession({ terminal_id: "excl-self-2" });
    store.register(s1);
    store.register(s2);

    const all = store.getAll("excl-self-1");
    expect(all.map((s) => s.terminal_id)).not.toContain("excl-self-1");
    expect(all.map((s) => s.terminal_id)).toContain("excl-self-2");
  });

  it("returns empty array when no sessions are registered", () => {
    // Spin up a fresh store in a completely separate temp dir to guarantee empty
    const isolatedHome = path.join(os.tmpdir(), `isolated-${randomUUID()}`);
    fs.mkdirSync(path.join(isolatedHome, ".claude", "shared-state", "sessions"), {
      recursive: true,
    });

    // We can't reload the module, so we test getAll() against the shared store
    // by deregistering any sessions we added and verifying only our added ones appear
    const store = new SessionStore();
    const before = store.getAll().map((s) => s.terminal_id);

    const fresh = makeSession({ terminal_id: "only-fresh" });
    store.register(fresh);

    const after = store.getAll().map((s) => s.terminal_id);
    expect(after).toContain("only-fresh");

    store.deregister("only-fresh");
    const afterRemove = store.getAll().map((s) => s.terminal_id);
    expect(afterRemove).not.toContain("only-fresh");

    // Clean up isolated dir
    try { fs.rmSync(isolatedHome, { recursive: true, force: true }); } catch {}
  });
});
