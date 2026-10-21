// ────── Versioned schema migrations ──────
// Numbered, up-only SQL files under ./migrations are applied once each,
// recorded in `panel_schema_migrations` with a SHA-256 checksum. Every file
// runs inside its own transaction. The runner executes during boot, before
// the HTTP listener starts, and refuses to start when an already-applied
// file changed (drift) or a pending file fails.
//
// Existing deployments that predate the runner are *baselined*: when a
// migration's marker table already exists, the migration is recorded as
// applied without re-running its (non-idempotent) policy statements.
import { promises as fs } from 'fs';
import crypto from 'crypto';
import path from 'path';
import { fileURLToPath } from 'url';
import { getPool } from './pool.ts';

const MIGRATIONS_DIR = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  'migrations'
);
const APPLIED_TABLE = 'panel_schema_migrations';

// Markers that identify an already-provisioned schema. A plain value is a
// table checked with to_regclass('public.<table>'); `table.column` checks
// information_schema instead (for additive ALTER migrations). Keep in sync
// with the migrations directory: every version that can be baselined gets an
// entry, so databases migrated by hand are recorded instead of re-executed.
const BASELINE_MARKERS: Record<number, string> = {
  1: 'docker_apps',
  2: 'rbac_instance_roles',
  3: 'sso_identities',
  4: 'api_keys.scopes',
  5: 'secrets.external_ref',
  6: 'panel_app_snapshots',
};

export interface MigrationFile {
  version: number;
  name: string;
  file: string;
  sql: string;
  checksum: string;
}

const sha256 = (sql: string): string =>
  crypto.createHash('sha256').update(sql).digest('hex');

export interface MigrationResult {
  applied: string[];
  baselined: string[];
  skipped: boolean;
  reason?: string;
}

export async function loadMigrations(): Promise<MigrationFile[]> {
  const entries = await fs.readdir(MIGRATIONS_DIR);
  const files = entries
    .filter((name) => /^\d+_[A-Za-z0-9_.-]+\.sql$/.test(name))
    .sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
  const migrations: MigrationFile[] = [];
  for (const file of files) {
    const sql = await fs.readFile(path.join(MIGRATIONS_DIR, file), 'utf-8');
    migrations.push({
      version: parseInt(file, 10),
      name: file.replace(/^\d+_/, '').replace(/\.sql$/, ''),
      file,
      sql,
      checksum: sha256(sql),
    });
  }
  const versions = migrations.map((m) => m.version);
  const duplicate = versions.find((v, i) => versions.indexOf(v) !== i);
  if (duplicate !== undefined) {
    throw new Error(`[db] duplicate migration version ${duplicate}`);
  }
  return migrations;
}

export async function runMigrations(): Promise<MigrationResult> {
  if (process.env.PANEL_AUTO_MIGRATE === 'false') {
    return {
      applied: [],
      baselined: [],
      skipped: true,
      reason: 'PANEL_AUTO_MIGRATE=false',
    };
  }
  const pool = getPool();
  if (!pool) {
    return {
      applied: [],
      baselined: [],
      skipped: true,
      reason: 'DATABASE_URL not set',
    };
  }

  const migrations = await loadMigrations();
  const client = await pool.connect();
  const applied: string[] = [];
  const baselined: string[] = [];
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS ${APPLIED_TABLE} (
        version INT PRIMARY KEY,
        name TEXT NOT NULL,
        checksum TEXT NOT NULL,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
      )
    `);
    const { rows } = await client.query(
      `SELECT version, name, checksum FROM ${APPLIED_TABLE}`
    );
    const recorded = new Map<number, { name: string; checksum: string }>(
      rows.map((row: any) => [
        Number(row.version),
        { name: String(row.name), checksum: String(row.checksum) },
      ])
    );

    for (const migration of migrations) {
      const previous = recorded.get(migration.version);
      if (previous) {
        // Baselined rows carry the synthetic 'baseline' checksum and are not
        // drift-checked; real applications must match byte-for-byte.
        if (
          previous.checksum !== 'baseline' &&
          previous.checksum !== migration.checksum
        ) {
          throw new Error(
            `[db] migration ${migration.version} (${migration.name}) changed after it was applied ` +
              '— restore the original file or add a new migration'
          );
        }
        continue;
      }

      const marker = BASELINE_MARKERS[migration.version];
      if (marker) {
        const [markerTable, markerColumn] = marker.split('.');
        const { rows: markerRows } = markerColumn
          ? await client.query(
              `SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = $1 AND column_name = $2`,
              [markerTable, markerColumn]
            )
          : await client.query('SELECT to_regclass($1) AS regclass', [
              `public.${markerTable}`,
            ]);
        const markerExists = markerColumn
          ? markerRows.length > 0
          : Boolean(markerRows[0]?.regclass);
        if (markerExists) {
          await client.query(
            `INSERT INTO ${APPLIED_TABLE} (version, name, checksum)
             VALUES ($1, $2, $3)`,
            [migration.version, migration.name, 'baseline']
          );
          baselined.push(migration.file);
          continue;
        }
      }

      await client.query('BEGIN');
      try {
        await client.query(migration.sql);
        await client.query(
          `INSERT INTO ${APPLIED_TABLE} (version, name, checksum)
           VALUES ($1, $2, $3)`,
          [migration.version, migration.name, migration.checksum]
        );
        await client.query('COMMIT');
        applied.push(migration.file);
      } catch (err) {
        await client.query('ROLLBACK').catch(() => undefined);
        throw new Error(
          `[db] migration ${migration.file} failed: ${
            err instanceof Error ? err.message : String(err)
          }`
        );
      }
    }
  } finally {
    client.release();
  }

  if (applied.length > 0 || baselined.length > 0) {
    console.log(
      `[db] migrations: applied ${applied.length}, baselined ${baselined.length}`
    );
  }
  return { applied, baselined, skipped: false };
}
