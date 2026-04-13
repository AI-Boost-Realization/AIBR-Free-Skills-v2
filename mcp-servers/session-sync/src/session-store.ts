import * as fs from "fs";
import * as path from "path";
import type { SessionInfo, BroadcastMessage, SyncEvent } from "./types.js";

const HOME = process.env.HOME || "/tmp";
const SESSIONS_DIR = path.join(HOME, ".claude", "shared-state", "sessions");
const BROADCAST_FILE = path.join(HOME, ".claude", "shared-state", "broadcasts.json");
const EVENT_LOG = path.join(HOME, ".claude", "shared-state", "event-log.jsonl");
const MAX_LOG_SIZE = 512 * 1024; // 500KB
const STALE_MS = 30 * 60 * 1000; // 30 minutes

export class SessionStore {
  constructor() {
    fs.mkdirSync(SESSIONS_DIR, { recursive: true });
  }

  private isAlive(pid: number): boolean {
    try {
      process.kill(pid, 0);
      return true;
    } catch (err: unknown) {
      // EPERM means process exists but we can't signal it (different user)
      if ((err as NodeJS.ErrnoException).code === "EPERM") return true;
      return false;
    }
  }

  private cleanStale(): void {
    const now = Date.now();
    for (const file of this.sessionFiles()) {
      try {
        const fp = path.join(SESSIONS_DIR, file);
        const s: SessionInfo = JSON.parse(fs.readFileSync(fp, "utf-8"));
        const age = now - new Date(s.heartbeat).getTime();
        if (age > STALE_MS || !this.isAlive(s.pid)) {
          fs.unlinkSync(fp);
        }
      } catch {
        try {
          fs.unlinkSync(path.join(SESSIONS_DIR, file));
        } catch {}
      }
    }
  }

  private sessionFiles(): string[] {
    try {
      return fs.readdirSync(SESSIONS_DIR).filter((f) => f.endsWith(".json"));
    } catch {
      return [];
    }
  }

  private readSession(file: string): SessionInfo | null {
    try {
      return JSON.parse(
        fs.readFileSync(path.join(SESSIONS_DIR, file), "utf-8")
      );
    } catch {
      return null;
    }
  }

  private writeSession(session: SessionInfo): void {
    const fp = path.join(SESSIONS_DIR, `${session.terminal_id}.json`);
    const tmp = fp + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(session, null, 2));
    fs.renameSync(tmp, fp);
  }

  register(session: SessionInfo): void {
    this.writeSession(session);
  }

  deregister(terminalId: string): boolean {
    const fp = path.join(SESSIONS_DIR, `${terminalId}.json`);
    try {
      fs.unlinkSync(fp);
      return true;
    } catch {
      return false;
    }
  }

  getAll(excludeId?: string): SessionInfo[] {
    this.cleanStale();
    const sessions: SessionInfo[] = [];
    for (const file of this.sessionFiles()) {
      const s = this.readSession(file);
      if (s && (!excludeId || s.terminal_id !== excludeId)) {
        sessions.push(s);
      }
    }
    return sessions;
  }

  get(terminalId: string): SessionInfo | null {
    return this.readSession(`${terminalId}.json`);
  }

  updateTask(terminalId: string, taskSummary: string): boolean {
    const s = this.get(terminalId);
    if (!s) return false;
    s.task_summary = taskSummary;
    s.heartbeat = new Date().toISOString();
    this.writeSession(s);
    return true;
  }

  claimFiles(terminalId: string, files: string[]): boolean {
    const s = this.get(terminalId);
    if (!s) return false;
    s.claimed_files = [...new Set([...(s.claimed_files || []), ...files])];
    s.heartbeat = new Date().toISOString();
    this.writeSession(s);
    return true;
  }

  checkFileConflicts(
    terminalId: string,
    files: string[]
  ): { file: string; owner: SessionInfo }[] {
    const conflicts: { file: string; owner: SessionInfo }[] = [];
    for (const s of this.getAll(terminalId)) {
      if (!s.claimed_files) continue;
      for (const f of files) {
        if (s.claimed_files.includes(f)) {
          conflicts.push({ file: f, owner: s });
        }
      }
    }
    return conflicts;
  }

  broadcast(from: string, message: string): void {
    let msgs: BroadcastMessage[] = [];
    try {
      msgs = JSON.parse(fs.readFileSync(BROADCAST_FILE, "utf-8"));
    } catch {}
    msgs.push({ from, timestamp: new Date().toISOString(), message });
    if (msgs.length > 50) msgs = msgs.slice(-50);
    const tmp = BROADCAST_FILE + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(msgs, null, 2));
    fs.renameSync(tmp, BROADCAST_FILE);
  }

  getRecentBroadcasts(since?: string): BroadcastMessage[] {
    try {
      const msgs: BroadcastMessage[] = JSON.parse(
        fs.readFileSync(BROADCAST_FILE, "utf-8")
      );
      if (since) {
        const cutoff = new Date(since).getTime();
        return msgs.filter((m) => new Date(m.timestamp).getTime() > cutoff);
      }
      return msgs.slice(-10);
    } catch {
      return [];
    }
  }

  // ── Event Log Methods ──────────────────────────────────────────────────

  private getNextSeq(): number {
    try {
      const content = fs.readFileSync(EVENT_LOG, "utf-8");
      const lines = content.trim().split("\n").filter(Boolean);
      if (lines.length === 0) return 1;
      const last = JSON.parse(lines[lines.length - 1]) as SyncEvent;
      return (last.seq || lines.length) + 1;
    } catch {
      return 1;
    }
  }

  emitEvent(
    sid: string,
    project: string,
    type: string,
    payload: Record<string, unknown>
  ): void {
    try {
      const event: SyncEvent = {
        seq: this.getNextSeq(),
        ts: new Date().toISOString(),
        sid,
        project,
        type,
        payload,
      };
      fs.appendFileSync(EVENT_LOG, JSON.stringify(event) + "\n");
    } catch {
      // Never throw — sync failures must not block work
    }
  }

  getEvents(opts: {
    since_seq?: number;
    since_time?: string;
    types?: string[];
    project?: string;
    limit?: number;
    excludeSid?: string;
  }): SyncEvent[] {
    try {
      const content = fs.readFileSync(EVENT_LOG, "utf-8");
      const lines = content.trim().split("\n").filter(Boolean);
      let events: SyncEvent[] = lines.map((l) => JSON.parse(l));

      if (opts.since_seq != null) {
        events = events.filter((e) => e.seq > opts.since_seq!);
      }
      if (opts.since_time) {
        const cutoff = new Date(opts.since_time).getTime();
        events = events.filter((e) => new Date(e.ts).getTime() > cutoff);
      }
      if (opts.types && opts.types.length > 0) {
        events = events.filter((e) => opts.types!.includes(e.type));
      }
      if (opts.project) {
        events = events.filter((e) => e.project === opts.project);
      }
      if (opts.excludeSid) {
        events = events.filter((e) => e.sid !== opts.excludeSid);
      }

      return events.slice(-(opts.limit || 50));
    } catch {
      return [];
    }
  }

  rotateIfNeeded(): void {
    try {
      const stat = fs.statSync(EVENT_LOG);
      if (stat.size > MAX_LOG_SIZE) {
        const date = new Date().toISOString().slice(0, 10);
        const archivePath = EVENT_LOG.replace(".jsonl", `.${date}.jsonl`);
        fs.renameSync(EVENT_LOG, archivePath);
      }
    } catch {
      // File may not exist yet
    }
  }
}
