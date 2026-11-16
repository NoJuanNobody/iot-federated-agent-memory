import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import type { ToolContext } from './index.js';

/** Where pulled docs and the manifest live inside the working folder. */
const NYX_DIR = '.nyx';
const DOCS_DIR = 'docs';
const MANIFEST_FILE = 'manifest.json';

/** One tracked doc's bookkeeping: where it lives locally + change-detection state. */
export interface ManifestEntry {
  /** Path to the local markdown copy, relative to cwd (POSIX separators). */
  localPath: string;
  title: string;
  /** Cloud `updatedAt` last synced — compared against the cloud to decide refreshes. */
  updatedAt: string;
  /** Hash of the last content we WROTE — compared against disk to detect local edits. */
  contentHash: string;
}

interface Manifest {
  /** docId → entry. */
  docs: Record<string, ManifestEntry>;
}

function nyxDir(cwd: string): string {
  return path.join(cwd, NYX_DIR);
}

function manifestFile(cwd: string): string {
  return path.join(nyxDir(cwd), MANIFEST_FILE);
}

/** Absolute path of a pulled doc, given its cwd-relative localPath. */
export function localDocPath(cwd: string, entry: ManifestEntry): string {
  return path.join(cwd, entry.localPath);
}

/** Stable content hash for local-edit detection. */
export function contentHash(content: string): string {
  return crypto.createHash('sha256').update(content, 'utf8').digest('hex');
}

/**
 * Read the manifest, degrading to an empty one if it's missing or malformed —
 * a corrupt manifest must never crash the agent or the poller.
 */
export function readManifest(cwd: string): Manifest {
  try {
    const parsed = JSON.parse(fs.readFileSync(manifestFile(cwd), 'utf8')) as Partial<Manifest>;
    const docs = parsed && typeof parsed.docs === 'object' && parsed.docs ? parsed.docs : {};
    return { docs: docs as Record<string, ManifestEntry> };
  } catch {
    return { docs: {} };
  }
}

/**
 * Read/merge/write a single manifest entry, mirroring the settings-writer
 * pattern in config.ts (addAllowRule). Creates `.nyx/` if absent.
 */
export function upsertManifestEntry(cwd: string, docId: string, entry: ManifestEntry): void {
  const manifest = readManifest(cwd);
  manifest.docs[docId] = entry;
  const dir = nyxDir(cwd);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(manifestFile(cwd), `${JSON.stringify(manifest, null, 2)}\n`, 'utf8');
}

/** A short, filesystem-safe slug derived from the doc title (falls back to id). */
function safeName(title: string, id: string): string {
  const slug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);
  const base = slug || 'doc';
  return `${base}-${id}`.replace(/[^a-z0-9-]/gi, '-');
}

/** Escape a value for a single-line YAML frontmatter field. */
function yamlValue(v: string): string {
  return `"${v.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

/** Build the markdown file body: YAML frontmatter header + the doc content. */
export function renderDocFile(meta: {
  id: string;
  title: string;
  stage?: string;
  path?: string;
  updatedAt?: string;
  content: string;
}): string {
  const fm: string[] = ['---'];
  fm.push(`id: ${yamlValue(meta.id)}`);
  fm.push(`title: ${yamlValue(meta.title)}`);
  if (meta.stage) fm.push(`stage: ${yamlValue(meta.stage)}`);
  if (meta.path) fm.push(`path: ${yamlValue(meta.path)}`);
  if (meta.updatedAt) fm.push(`updatedAt: ${yamlValue(meta.updatedAt)}`);
  fm.push('---', '');
  return `${fm.join('\n')}\n${meta.content}`;
}

/** Parsed fields from a Nyx document JSON response. */
export interface NyxDoc {
  id: string;
  title: string;
  stage?: string;
  path?: string;
  updatedAt?: string;
  content: string;
}

/** Pull the `content`/metadata fields out of a doc JSON payload, if valid. */
export function parseNyxDoc(raw: string, fallbackId: string): NyxDoc | null {
  let doc: Record<string, unknown>;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return null;
    doc = parsed as Record<string, unknown>;
  } catch {
    return null;
  }
  const str = (v: unknown): string | undefined =>
    typeof v === 'string' ? v : v != null && typeof v !== 'object' ? String(v) : undefined;
  return {
    id: str(doc.id) || fallbackId,
    title: str(doc.title) || fallbackId,
    stage: str(doc.stage),
    path: str(doc.path),
    updatedAt: str(doc.updatedAt),
    content: typeof doc.content === 'string' ? doc.content : '',
  };
}

/**
 * Write a pulled doc to `<cwd>/.nyx/docs/<safe-name>.md` and update the manifest.
 * Returns the cwd-relative local path. Reuses an existing entry's localPath when
 * re-pulling so the file location stays stable.
 */
export function writePulledDoc(cwd: string, doc: NyxDoc): ManifestEntry {
  const existing = readManifest(cwd).docs[doc.id];
  const relPath = existing?.localPath ?? path.posix.join(NYX_DIR, DOCS_DIR, `${safeName(doc.title, doc.id)}.md`);
  const abs = path.join(cwd, relPath);
  const body = renderDocFile(doc);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, body, 'utf8');
  const entry: ManifestEntry = {
    localPath: relPath,
    title: doc.title,
    updatedAt: doc.updatedAt ?? '',
    contentHash: contentHash(body),
  };
  upsertManifestEntry(cwd, doc.id, entry);
  return entry;
}

/** Read the on-disk hash of a tracked file, or null if it's missing/unreadable. */
function diskHash(cwd: string, entry: ManifestEntry): string | null {
  try {
    return contentHash(fs.readFileSync(localDocPath(cwd, entry), 'utf8'));
  } catch {
    return null;
  }
}

/** Outcome of a single sync pass, summarized for an info line. */
export interface SyncResult {
  /** Number of local files refreshed from the cloud. */
  synced: number;
  /** Titles of docs skipped because of local edits (hash mismatch). */
  skippedLocalEdits: string[];
}

/**
 * One background sync pass: for each tracked doc, fetch the cloud copy and, if
 * the cloud `updatedAt` is newer than the manifest's, rewrite the local file —
 * UNLESS the on-disk file was locally edited (hash differs from the stored
 * contentHash), in which case skip it with a warning. Failures are swallowed per
 * doc so a flaky backend produces no error storm. Caller must have already
 * checked that Nyx is configured and the manifest is non-empty.
 */
export async function syncTrackedDocs(
  cwd: string,
  ctx: ToolContext,
  fetchDoc: (id: string) => Promise<string>,
): Promise<SyncResult> {
  const result: SyncResult = { synced: 0, skippedLocalEdits: [] };
  const manifest = readManifest(cwd);
  for (const [id, entry] of Object.entries(manifest.docs)) {
    let raw: string;
    try {
      raw = await fetchDoc(id);
    } catch {
      continue; // backend hiccup — stay quiet
    }
    const doc = parseNyxDoc(raw, id);
    if (!doc) continue;
    // Cloud not newer → nothing to do.
    if (!doc.updatedAt || doc.updatedAt <= entry.updatedAt) continue;
    // Local-edit guard: if the file on disk differs from what we last wrote,
    // the user changed it — never clobber, surface a warning instead.
    const onDisk = diskHash(cwd, entry);
    if (onDisk !== null && onDisk !== entry.contentHash) {
      result.skippedLocalEdits.push(entry.title || id);
      continue;
    }
    try {
      writePulledDoc(cwd, doc);
      result.synced += 1;
    } catch {
      // Disk write failed — skip quietly.
    }
  }
  return result;
}

/** Number of tracked docs — the poller stays off when this is 0. */
export function trackedDocCount(cwd: string): number {
  return Object.keys(readManifest(cwd).docs).length;
}
