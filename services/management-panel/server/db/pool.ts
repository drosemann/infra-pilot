// ────── Panel database pool ──────
// One lazy pg pool shared by the migration runner and the persistent state
// stores. `DATABASE_URL` is the same PostgreSQL the orchestrator uses in
// Compose; against hosted Supabase it must point at the project's direct
// Postgres connection string (the REST client keeps handling auth).
import pg from 'pg';

// pg is CommonJS and exports the module instance; named ESM imports are not
// statically detectable, so bind the constructor off the default export.
let pool: any = null;
let warnedMissing = false;

export const databaseUrlConfigured = (): boolean => Boolean(process.env.DATABASE_URL);

export function getPool(): any {
  if (!process.env.DATABASE_URL) {
    if (!warnedMissing) {
      warnedMissing = true;
      console.warn(
        '[db] DATABASE_URL is not set — persistent state falls back to process memory'
      );
    }
    return null;
  }
  if (!pool) {
    pool = new pg.Pool({
      connectionString: process.env.DATABASE_URL,
      max: Number(process.env.PG_POOL_MAX) || 8,
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 10_000,
    });
    pool.on('error', (err: any) => {
      console.error('[db] idle client error:', err?.message || err);
    });
  }
  return pool;
}

export async function closePool(): Promise<void> {
  if (!pool) return;
  const current = pool;
  pool = null;
  await current.end().catch(() => undefined);
}
