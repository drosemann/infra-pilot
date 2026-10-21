-- ============================================================================
-- Phase 7: SSO / OIDC (server/sso/)
-- ============================================================================
-- EXTERNAL IdP logins link to Supabase auth users through `sso_identities`
-- (JIT provisioning requires the panel's service-role key). Panel sessions
-- (cookie + `sso_...` Bearer tokens) persist server-side so they are
-- revocable; group claims map to instance roles through `sso_group_roles`
-- and are applied only when the user has no admin-set role yet.

CREATE TABLE IF NOT EXISTS sso_identities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider VARCHAR(50) NOT NULL,
  sub TEXT NOT NULL,
  email TEXT NOT NULL,
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  display_name TEXT,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  groups JSONB,
  last_login_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(provider, sub)
);
CREATE INDEX IF NOT EXISTS idx_sso_identities_user
  ON sso_identities (user_id);

CREATE TABLE IF NOT EXISTS panel_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  provider VARCHAR(50) NOT NULL,
  revoked BOOLEAN NOT NULL DEFAULT FALSE,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  last_seen_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_panel_sessions_user
  ON panel_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_panel_sessions_expiry
  ON panel_sessions (expires_at);

CREATE TABLE IF NOT EXISTS sso_group_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider VARCHAR(50) NOT NULL CHECK (provider IN ('google', 'microsoft', 'oidc')),
  group_name VARCHAR(200) NOT NULL,
  role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(provider, group_name)
);

-- Row security: the panel service connection performs all writes (service
-- role bypasses RLS); users may read only their own rows.
ALTER TABLE sso_identities ENABLE ROW LEVEL SECURITY;
ALTER TABLE panel_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sso_group_roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "SSO identities readable by their user" ON sso_identities
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Panel sessions readable by their user" ON panel_sessions
  FOR SELECT USING (auth.uid() = user_id);
-- Group mappings are instance configuration: readable by authenticated
-- users so settings pages can render; writable only via the panel server.
CREATE POLICY "Group role mappings readable by authenticated users" ON sso_group_roles
  FOR SELECT USING (auth.role() = 'authenticated');
