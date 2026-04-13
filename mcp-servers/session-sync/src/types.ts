export interface SessionInfo {
  terminal_id: string;
  pid: number;
  directory: string;
  project: string;
  started: string;
  heartbeat: string;
  status: "active" | "idle" | "busy";
  task_summary: string;
  tools_used: number;
  claimed_files?: string[];
  event_cursor?: number;
}

export interface BroadcastMessage {
  from: string;
  timestamp: string;
  message: string;
}

export interface SyncEvent {
  seq: number;
  ts: string;
  sid: string;
  project: string;
  type: string;
  payload: Record<string, unknown>;
}
