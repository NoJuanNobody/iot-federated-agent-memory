import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions';

/**
 * Sessions are stored append-only as JSON Lines under
 *   ~/.dsx/sessions/<cwd-hash>/<session-id>.jsonl
 * One JSON object per line. The cwd is hashed into the path so sessions from
 * different working directories never bleed into one another's --resume.
 */

/** Root directory holding all sessions, partitioned by cwd hash. */
function sessionsRoot(): string {
  return path.join(os.homedir(), '.dsx', 'sessions');
}

/** Stable short identifier for a working directory: sha256(cwd) hex, first 12 chars. */
export function cwdHash(cwd: string): string {
  return crypto.createHash('sha256').update(path.resolve(cwd)).digest('hex').slice(0, 12);
}

/** Directory that holds every session file for a given cwd. */
function sessionDir(cwd: string): string {
  return path.join(sessionsRoot(), cwdHash(cwd));
}

function sessionFile(cwd: string, id: string): string {
  return path.join(sessionDir(cwd), `${id}.jsonl`);
}

/** Generate a sortable, collision-resistant session id (timestamp + random). */
function newSessionId(): string {
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  return `${ts}-${crypto.randomBytes(3).toString('hex')}`;
}

export interface Session {
  id: string;
  cwd: string;
  /** Absolute path to the backing .jsonl file. */
  file: string;
}

/** Create a fresh, empty session file for the cwd and return its handle. */
export function createSession(cwd: string, id: string = newSessionId()): Session {
  const dir = sessionDir(cwd);
  fs.mkdirSync(dir, { recursive: true });
  const file = sessionFile(cwd, id);
  // Touch the file so an empty session still shows up in listings.
  fs.writeFileSync(file, '', { flag: 'a' });
  return { id, cwd, file };
}

/** Append one message as a single JSON line. Crash-safe: each turn is durable as it completes. */
export function appendMessage(session: Session, message: ChatCompletionMessageParam): void {
  fs.appendFileSync(session.file, `${JSON.stringify(message)}\n`);
}

/** Parse a .jsonl session file into its messages, skipping blank/corrupt lines. */
function readMessages(file: string): ChatCompletionMessageParam[] {
  let raw: string;
  try {
    raw = fs.readFileSync(file, 'utf8');
  } catch {
    return [];
  }
  const messages: ChatCompletionMessageParam[] = [];
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      messages.push(JSON.parse(trimmed) as ChatCompletionMessageParam);
    } catch {
      // Skip a partially-written final line (e.g. after a crash mid-append).
    }
  }
  return messages;
}

export interface SessionInfo {
  id: string;
  file: string;
  /** Last modification time, used for sorting "latest". */
  mtime: Date;
  /** Number of persisted messages. */
  messageCount: number;
}

/** List sessions for the cwd, newest first. */
export function listSessions(cwd: string): SessionInfo[] {
  const dir = sessionDir(cwd);
  let names: string[];
  try {
    names = fs.readdirSync(dir);
  } catch {
    return [];
  }
  const infos: SessionInfo[] = [];
  for (const name of names) {
    if (!name.endsWith('.jsonl')) continue;
    const file = path.join(dir, name);
    let mtime: Date;
    try {
      mtime = fs.statSync(file).mtime;
    } catch {
      continue;
    }
    infos.push({
      id: name.slice(0, -'.jsonl'.length),
      file,
      mtime,
      messageCount: readMessages(file).length,
    });
  }
  return infos.sort((a, b) => b.mtime.getTime() - a.mtime.getTime());
}

export interface LoadedSession {
  session: Session;
  messages: ChatCompletionMessageParam[];
}

/** Load a specific session by id for the cwd, or null if it doesn't exist. */
export function loadSession(cwd: string, id: string): LoadedSession | null {
  const file = sessionFile(cwd, id);
  if (!fs.existsSync(file)) return null;
  return { session: { id, cwd, file }, messages: readMessages(file) };
}

/** Load the most recently modified session for the cwd, or null if none exist. */
export function latestSession(cwd: string): LoadedSession | null {
  const [newest] = listSessions(cwd);
  if (!newest) return null;
  return loadSession(cwd, newest.id);
}
