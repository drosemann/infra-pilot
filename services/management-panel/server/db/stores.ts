// ────── Persistent panel state ──────
// Durable stores replacing the in-memory Maps (snapshots, workspaces plugin
// installations) and the file-backed dashboard store. Backed by the shared
// pg pool (migration 006); when DATABASE_URL is unset a process-memory
// fallback keeps local development working with a warning. Reads are cached
// for PANEL_STATE_CACHE_TTL_MS and invalidated on every write.
import crypto from 'crypto';
import { promises as fs } from 'fs';
import { getPool } from './pool.ts';

const CACHE_TTL_MS = Number(process.env.PANEL_STATE_CACHE_TTL_MS) || 15_000;

interface CacheEntry {
  value: unknown;
  at: number;
}

const cache = new Map<string, CacheEntry>();
const memorySnapshots = new Map<string, any[]>();
const memoryWorkspaces = new Map<string, any[]>();
const memoryPlugins = new Map<string, any[]>();
const memoryDashboards = new Map<string, any>();

function cacheGet<T>(key: string): T | null {
  const hit = cache.get(key);
  if (!hit) return null;
  if (Date.now() - hit.at > CACHE_TTL_MS) {
    cache.delete(key);
    return null;
  }
  return hit.value as T;
}

function cacheSet(key: string, value: unknown): void {
  cache.set(key, { value, at: Date.now() });
}

function cacheDrop(...keys: string[]): void {
  for (const key of keys) cache.delete(key);
}

export function clearStateCache(): void {
  cache.clear();
}

// ---------------------------------------------------------------------------
// Snapshots
// ---------------------------------------------------------------------------

export function createDefaultSnapshots(appId: string): any[] {
  const now = Date.now();
  return [
    {
      id: crypto.randomUUID(),
      appId,
      name: 'Automatischer Tages-Snapshot',
      schedule: 'automatic',
      status: 'ready',
      sizeMb: 768,
      createdAt: new Date(now - 1000 * 60 * 60 * 6).toISOString(),
    },
    {
      id: crypto.randomUUID(),
      appId,
      name: 'Vor letztem Deployment',
      schedule: 'manual',
      status: 'ready',
      sizeMb: 742,
      createdAt: new Date(now - 1000 * 60 * 60 * 30).toISOString(),
    },
  ];
}

const mapSnapshot = (row: any): any => ({
  id: row.id,
  appId: row.app_id,
  name: row.name,
  schedule: row.schedule,
  status: row.status,
  sizeMb: row.size_mb,
  createdAt: new Date(row.created_at).toISOString(),
  ...(row.restored_at
    ? { restoredAt: new Date(row.restored_at).toISOString() }
    : {}),
});

export async function listSnapshots(appId: string): Promise<any[]> {
  const key = `snapshots:${appId}`;
  const cached = cacheGet<any[]>(key);
  if (cached) return cached;

  const pool = getPool();
  let rows: any[];
  if (!pool) {
    if (!memorySnapshots.has(appId)) {
      memorySnapshots.set(appId, createDefaultSnapshots(appId));
    }
    rows = memorySnapshots.get(appId) || [];
  } else {
    const result = await pool.query(
      'SELECT * FROM panel_app_snapshots WHERE app_id = $1 ORDER BY created_at DESC',
      [appId]
    );
    if (result.rows.length === 0) {
      const defaults = createDefaultSnapshots(appId);
      for (const snapshot of defaults) {
        await pool.query(
          `INSERT INTO panel_app_snapshots (id, app_id, name, schedule, status, size_mb, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (id) DO NOTHING`,
          [
            snapshot.id,
            appId,
            snapshot.name,
            snapshot.schedule,
            snapshot.status,
            snapshot.sizeMb,
            snapshot.createdAt,
          ]
        );
      }
      rows = defaults;
    } else {
      rows = result.rows.map(mapSnapshot);
    }
  }
  cacheSet(key, rows);
  return rows;
}

export async function createSnapshot(snapshot: any): Promise<any> {
  const pool = getPool();
  if (!pool) {
    memorySnapshots.set(snapshot.appId, [
      snapshot,
      ...(memorySnapshots.get(snapshot.appId) || []),
    ]);
  } else {
    await pool.query(
      `INSERT INTO panel_app_snapshots (id, app_id, name, schedule, status, size_mb, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [
        snapshot.id,
        snapshot.appId,
        snapshot.name,
        snapshot.schedule,
        snapshot.status,
        snapshot.sizeMb,
        snapshot.createdAt,
      ]
    );
  }
  cacheDrop(`snapshots:${snapshot.appId}`);
  return snapshot;
}

export async function restoreSnapshot(
  appId: string,
  snapshotId: string
): Promise<any | null> {
  const pool = getPool();
  if (!pool) {
    const snapshots = memorySnapshots.get(appId) || [];
    const snapshot = snapshots.find((item) => item.id === snapshotId);
    if (!snapshot) return null;
    snapshot.status = 'restoring';
    snapshot.restoredAt = new Date().toISOString();
    cacheDrop(`snapshots:${appId}`);
    return snapshot;
  }
  const result = await pool.query(
    `UPDATE panel_app_snapshots
     SET status = 'restoring', restored_at = now()
     WHERE id = $1 AND app_id = $2
     RETURNING *`,
    [snapshotId, appId]
  );
  cacheDrop(`snapshots:${appId}`);
  return result.rows.length ? mapSnapshot(result.rows[0]) : null;
}

export async function countSnapshots(appId: string): Promise<number> {
  const pool = getPool();
  if (!pool) return (await listSnapshots(appId)).length;
  const result = await pool.query(
    'SELECT count(*)::int AS count FROM panel_app_snapshots WHERE app_id = $1',
    [appId]
  );
  return Number(result.rows[0]?.count || 0);
}

// ---------------------------------------------------------------------------
// Workspaces
// ---------------------------------------------------------------------------

const mapWorkspace = (row: any): any => ({
  id: row.id,
  name: row.name,
  appIds: row.app_ids || [],
  memberCount: row.member_count,
  sharedBackups: row.shared_backups,
  sharedLogs: row.shared_logs,
  createdAt: new Date(row.created_at).toISOString(),
});

export async function listWorkspaces(userId: string): Promise<any[]> {
  const key = `workspaces:${userId}`;
  const cached = cacheGet<any[]>(key);
  if (cached) return cached;

  const pool = getPool();
  let rows: any[];
  if (!pool) {
    if (!memoryWorkspaces.has(userId)) memoryWorkspaces.set(userId, [defaultWorkspace()]);
    rows = memoryWorkspaces.get(userId) || [];
  } else {
    const result = await pool.query(
      'SELECT * FROM panel_workspaces WHERE user_id = $1 ORDER BY created_at DESC',
      [userId]
    );
    if (result.rows.length === 0) {
      const workspace = defaultWorkspace();
      await pool.query(
        `INSERT INTO panel_workspaces (id, user_id, name, app_ids, member_count, shared_backups, shared_logs, created_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [
          workspace.id,
          userId,
          workspace.name,
          JSON.stringify(workspace.appIds),
          workspace.memberCount,
          workspace.sharedBackups,
          workspace.sharedLogs,
          workspace.createdAt,
        ]
      );
      rows = [workspace];
    } else {
      rows = result.rows.map(mapWorkspace);
    }
  }
  cacheSet(key, rows);
  return rows;
}

function defaultWorkspace(): any {
  return {
    id: crypto.randomUUID(),
    name: 'Default Workspace',
    appIds: [],
    memberCount: 1,
    sharedBackups: true,
    sharedLogs: true,
    createdAt: new Date().toISOString(),
  };
}

export async function createWorkspace(userId: string, workspace: any): Promise<any> {
  const pool = getPool();
  if (!pool) {
    memoryWorkspaces.set(userId, [workspace, ...(memoryWorkspaces.get(userId) || [])]);
  } else {
    await pool.query(
      `INSERT INTO panel_workspaces (id, user_id, name, app_ids, member_count, shared_backups, shared_logs, created_at)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
      [
        workspace.id,
        userId,
        workspace.name,
        JSON.stringify(workspace.appIds || []),
        workspace.memberCount,
        workspace.sharedBackups,
        workspace.sharedLogs,
        workspace.createdAt,
      ]
    );
  }
  cacheDrop(`workspaces:${userId}`);
  return workspace;
}

// ---------------------------------------------------------------------------
// Plugin installations
// ---------------------------------------------------------------------------

export async function installPlugin(appId: string, installation: any): Promise<any> {
  const pool = getPool();
  if (!pool) {
    memoryPlugins.set(appId, [
      installation,
      ...(memoryPlugins.get(appId) || []).filter(
        (item) => item.pluginId !== installation.pluginId
      ),
    ]);
  } else {
    await pool.query(
      `INSERT INTO panel_plugin_installations (app_id, plugin_id, status, installed_at)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (app_id, plugin_id)
       DO UPDATE SET status = EXCLUDED.status, installed_at = EXCLUDED.installed_at`,
      [appId, installation.pluginId, installation.status, installation.installedAt]
    );
  }
  cacheDrop(`plugins:${appId}`);
  return installation;
}

// ---------------------------------------------------------------------------
// Dashboards
// ---------------------------------------------------------------------------

const mapDashboard = (row: any): any => ({ ...(row.data || {}), id: row.id });

export async function listDashboards(): Promise<any[]> {
  const cached = cacheGet<any[]>('dashboards:list');
  if (cached) return cached;

  const pool = getPool();
  let rows: any[];
  if (!pool) {
    rows = Array.from(memoryDashboards.values());
  } else {
    const result = await pool.query(
      'SELECT id, data FROM panel_dashboards ORDER BY created_at ASC'
    );
    rows = result.rows.map(mapDashboard);
  }
  cacheSet('dashboards:list', rows);
  return rows;
}

export async function getDashboard(id: string): Promise<any | null> {
  const cached = cacheGet<any>(`dashboards:${id}`);
  if (cached) return cached;

  const pool = getPool();
  let dashboard: any | null;
  if (!pool) {
    dashboard = memoryDashboards.get(id) || null;
  } else {
    const result = await pool.query(
      'SELECT id, data FROM panel_dashboards WHERE id = $1',
      [id]
    );
    dashboard = result.rows.length ? mapDashboard(result.rows[0]) : null;
  }
  if (dashboard) cacheSet(`dashboards:${id}`, dashboard);
  return dashboard;
}

export async function createDashboard(dashboard: any): Promise<any> {
  const pool = getPool();
  if (!pool) {
    memoryDashboards.set(dashboard.id, dashboard);
  } else {
    await pool.query(
      'INSERT INTO panel_dashboards (id, data) VALUES ($1, $2)',
      [dashboard.id, JSON.stringify(dashboard)]
    );
  }
  cacheDrop('dashboards:list');
  return dashboard;
}

export async function updateDashboard(
  id: string,
  patch: Record<string, unknown>
): Promise<any | null> {
  const existing = await getDashboard(id);
  if (!existing) return null;
  const updated = {
    ...existing,
    ...patch,
    id,
    updatedAt: new Date().toISOString(),
  };
  const pool = getPool();
  if (!pool) {
    memoryDashboards.set(id, updated);
  } else {
    await pool.query(
      'UPDATE panel_dashboards SET data = $2, updated_at = now() WHERE id = $1',
      [id, JSON.stringify(updated)]
    );
  }
  cacheDrop('dashboards:list', `dashboards:${id}`);
  return updated;
}

export async function deleteDashboard(id: string): Promise<boolean> {
  const pool = getPool();
  if (!pool) {
    const existed = memoryDashboards.delete(id);
    cacheDrop('dashboards:list');
    return existed;
  }
  const result = await pool.query(
    'DELETE FROM panel_dashboards WHERE id = $1',
    [id]
  );
  cacheDrop('dashboards:list', `dashboards:${id}`);
  return (result.rowCount || 0) > 0;
}

/**
 * One-time import of the legacy `data/dashboards.json` file. Only runs when
 * the table is empty; re-running is a no-op. Returns the number of imported
 * dashboards.
 */
export async function importDashboardsFromFile(filePath: string): Promise<number> {
  const pool = getPool();
  if (!pool) return 0;
  const { rows } = await pool.query('SELECT count(*)::int AS count FROM panel_dashboards');
  if (Number(rows[0]?.count || 0) > 0) return 0;
  let parsed: unknown;
  try {
    parsed = JSON.parse(await fs.readFile(filePath, 'utf-8'));
  } catch {
    return 0;
  }
  if (!Array.isArray(parsed)) return 0;
  let imported = 0;
  for (const item of parsed) {
    if (!item || typeof item !== 'object' || !(item as any).id) continue;
    await pool.query(
      'INSERT INTO panel_dashboards (id, data) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING',
      [String((item as any).id), JSON.stringify(item)]
    );
    imported += 1;
  }
  if (imported > 0) cacheDrop('dashboards:list');
  return imported;
}
