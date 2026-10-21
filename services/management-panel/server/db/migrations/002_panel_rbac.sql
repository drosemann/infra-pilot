-- ============================================================================
-- Phase 6: Panel RBAC (server/rbac/)
-- ============================================================================
-- Instance-level roles govern cross-user and instance resources (audit,
-- members, billing). App-level roles delegate another user's app without
-- transferring ownership. The server stores one authoritative row per
-- (user) and (app, principal) pair; role/service-account assignments live
-- in services/orchestrator-agent rbac tables (see wiki/11-Auth-Matrix.md).

CREATE TABLE IF NOT EXISTS rbac_instance_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
  granted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id)
);
CREATE INDEX IF NOT EXISTS idx_rbac_instance_roles_role
  ON rbac_instance_roles (role);

CREATE TABLE IF NOT EXISTS rbac_app_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  app_id UUID NOT NULL REFERENCES docker_apps(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role VARCHAR(50) NOT NULL
    CHECK (role IN ('admin', 'operator', 'viewer', 'custom', 'owner')),
  permissions JSONB DEFAULT '{}',
  granted_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(app_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_rbac_app_roles_app
  ON rbac_app_roles (app_id);

-- Row security: regular users may read assignments that concern them and
-- never modify them directly; the panel service connection performs all
-- writes through the server (service-role key bypasses RLS).
ALTER TABLE rbac_instance_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE rbac_app_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own instance role" ON rbac_instance_roles
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can view app roles concerning them" ON rbac_app_roles
  FOR SELECT USING (
    auth.uid() = user_id
    OR EXISTS (
      SELECT 1 FROM docker_apps
      WHERE docker_apps.id = rbac_app_roles.app_id
        AND docker_apps.user_id = auth.uid()
    )
  );
