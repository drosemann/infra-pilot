-- ============================================================================
-- Phase 8: Scoped API keys (server/apikeys/)
-- ============================================================================
-- Key model v2: every key carries a scope list (`apps:read`, `metrics:*`,
-- `*`), an optional live/test class key prefix (`ip_live_`/`ip_test_`),
-- an optional app binding, and rotation bookkeeping. Legacy rows keep
-- working with an implicit `*` scope and are prompted to rotate
-- (`force_rotate` or a NULL scopes array => needs_rotation).

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS scopes TEXT[] DEFAULT '{*}';
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_class VARCHAR(10)
  CHECK (key_class IN ('live', 'test'));
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS app_id UUID
  REFERENCES docker_apps(id) ON DELETE SET NULL;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS rotated_from UUID;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS force_rotate BOOLEAN
  NOT NULL DEFAULT FALSE;
ALTER TABLE api_keys ALTER COLUMN key_prefix TYPE VARCHAR(20);
CREATE INDEX IF NOT EXISTS idx_api_keys_user
  ON api_keys (user_id);
