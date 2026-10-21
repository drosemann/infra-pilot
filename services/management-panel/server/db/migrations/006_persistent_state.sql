-- 006_persistent_state.sql
-- Durable replacements for the panel's in-memory Maps and the file-backed
-- dashboard store. Rows are panel-owned state (no auth.users foreign keys)
-- so the same tables work in Supabase and local-Postgres mode. The RBAC
-- store from the previous wave already persists per-app roles in
-- rbac_role_assignments, so no extra table is needed for that map.

CREATE TABLE IF NOT EXISTS panel_app_snapshots (
  id UUID PRIMARY KEY,
  app_id UUID NOT NULL,
  name TEXT NOT NULL,
  schedule TEXT NOT NULL CHECK (schedule IN ('manual', 'automatic')),
  status TEXT NOT NULL DEFAULT 'ready',
  size_mb INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  restored_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_panel_app_snapshots_app
  ON panel_app_snapshots (app_id, created_at DESC);

CREATE TABLE IF NOT EXISTS panel_workspaces (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  name TEXT NOT NULL,
  app_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
  member_count INT NOT NULL DEFAULT 1,
  shared_backups BOOLEAN NOT NULL DEFAULT TRUE,
  shared_logs BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_panel_workspaces_user
  ON panel_workspaces (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS panel_plugin_installations (
  app_id UUID NOT NULL,
  plugin_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'installed',
  installed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (app_id, plugin_id)
);

CREATE TABLE IF NOT EXISTS panel_dashboards (
  id TEXT PRIMARY KEY,
  data JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
