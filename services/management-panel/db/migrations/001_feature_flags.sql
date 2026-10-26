-- Feature flags: panel is the single source of truth.
-- Apply after schema.sql (or run standalone on an existing DB).
CREATE TABLE IF NOT EXISTS feature_flags (
  key VARCHAR(255) PRIMARY KEY CHECK (key ~ '^[a-z][a-z0-9_.-]{1,63}$'),
  description TEXT NOT NULL DEFAULT '',
  value_type VARCHAR(20) NOT NULL DEFAULT 'boolean' CHECK (value_type IN ('boolean', 'variant')),
  default_value JSONB NOT NULL DEFAULT 'false',
  variants JSONB,
  fail_mode VARCHAR(10) NOT NULL DEFAULT 'closed' CHECK (fail_mode IN ('closed', 'open')),
  status VARCHAR(10) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
  expires_at TIMESTAMP WITH TIME ZONE,
  created_by UUID REFERENCES auth.users (id) ON DELETE SET NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feature_flag_rules (
  flag_key VARCHAR(255) NOT NULL REFERENCES feature_flags (key) ON DELETE CASCADE,
  environment VARCHAR(20) NOT NULL CHECK (environment IN ('development', 'staging', 'production')),
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  rollout_percentage INT NOT NULL DEFAULT 0 CHECK (rollout_percentage BETWEEN 0 AND 100),
  target_org_ids JSONB NOT NULL DEFAULT '[]',
  target_project_ids JSONB NOT NULL DEFAULT '[]',
  target_user_ids JSONB NOT NULL DEFAULT '[]',
  deny_user_ids JSONB NOT NULL DEFAULT '[]',
  updated_by UUID REFERENCES auth.users (id) ON DELETE SET NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (flag_key, environment)
);

INSERT INTO feature_flags (key, description, default_value) VALUES
  ('discord_service_v2', 'New Discord command set (v2 commands).', 'false'),
  ('living_fleet', 'Living-fleet creature UX and mood engine.', 'false')
ON CONFLICT (key) DO NOTHING;
