-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Setup Configuration
CREATE TABLE IF NOT EXISTS setup_config (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  mode VARCHAR(50) NOT NULL DEFAULT 'personal' CHECK (mode IN ('personal', 'business')),
  initialized BOOLEAN NOT NULL DEFAULT FALSE,
  admin_user_id UUID,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_user_id) REFERENCES auth.users (id) ON DELETE SET NULL
);

-- User Profiles
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name VARCHAR(255),
  avatar_url VARCHAR(1000),
  role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
  mode_at_signup VARCHAR(50) DEFAULT 'personal',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Docker Apps
CREATE TABLE IF NOT EXISTS docker_apps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  image VARCHAR(500) NOT NULL,
  status VARCHAR(50) DEFAULT 'stopped' CHECK (status IN ('running', 'stopped', 'restarting', 'error')),
  container_id VARCHAR(255),
  ports JSONB, -- [{hostPort: 8080, containerPort: 8000, protocol: 'tcp'}, ...]
  environment_vars JSONB, -- {KEY: value, ...}
  volumes JSONB, -- [{hostPath: '/data', containerPath: '/app/data'}, ...]
  restart_policy VARCHAR(50) DEFAULT 'no' CHECK (restart_policy IN ('no', 'always', 'unless-stopped', 'on-failure')),
  memory_limit VARCHAR(50), -- e.g., '512m', '1g'
  cpu_shares INT,
  description TEXT,
  labels JSONB, -- {tier: 'production', team: 'web', ...}
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  started_at TIMESTAMP WITH TIME ZONE,
  INDEX idx_user_id (user_id),
  INDEX idx_status (status)
);

-- App Logs (optional: for log streaming)
CREATE TABLE IF NOT EXISTS app_logs (
  id BIGSERIAL PRIMARY KEY,
  app_id UUID NOT NULL REFERENCES docker_apps(id) ON DELETE CASCADE,
  level VARCHAR(20) DEFAULT 'info' CHECK (level IN ('debug', 'info', 'warn', 'error')),
  message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_app_id_created (app_id, created_at DESC)
);

-- Pterodactyl Configuration (for optional remote panel support)
CREATE TABLE IF NOT EXISTS pterodactyl_config (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  api_key VARCHAR(255) NOT NULL,
  panel_url VARCHAR(1000) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id)
);

-- Shared Configuration (for setup wizard settings, feature flags, etc.)
CREATE TABLE IF NOT EXISTS shared_config (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  key VARCHAR(255) NOT NULL UNIQUE,
  value JSONB NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- RLS Policies
ALTER TABLE docker_apps ENABLE ROW LEVEL SECURITY;
ALTER TABLE app_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pterodactyl_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- MVP Customers table (Business Mode)
CREATE TABLE IF NOT EXISTS customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Customers RLS
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view their own customers" ON customers
FOR SELECT USING (auth.uid() = owner_user_id);
CREATE POLICY "Users can insert their own customers" ON customers
FOR INSERT WITH CHECK (auth.uid() = owner_user_id);
CREATE POLICY "Users can update their own customers" ON customers
FOR UPDATE USING (auth.uid() = owner_user_id);
CREATE POLICY "Users can delete their own customers" ON customers
FOR DELETE USING (auth.uid() = owner_user_id);

-- Docker Apps RLS
CREATE POLICY "Users can view their own apps" ON docker_apps
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own apps" ON docker_apps
FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own apps" ON docker_apps
FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own apps" ON docker_apps
FOR DELETE USING (auth.uid() = user_id);

-- App Logs RLS
CREATE POLICY "Users can view logs for their apps" ON app_logs
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM docker_apps
    WHERE docker_apps.id = app_logs.app_id
    AND docker_apps.user_id = auth.uid()
  )
);

-- Pterodactyl Config RLS
CREATE POLICY "Users can view their own pterodactyl config" ON pterodactyl_config
FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own pterodactyl config" ON pterodactyl_config
FOR UPDATE USING (auth.uid() = user_id);

-- User Profiles RLS
CREATE POLICY "Users can view their own profile" ON user_profiles
FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON user_profiles
FOR UPDATE USING (auth.uid() = id);

-- ============================================================================
-- Phase 4: Management Panel Tables
-- ============================================================================

-- Server Metrics (TPS, player count, world size, lag spikes)
CREATE TABLE IF NOT EXISTS server_metrics (
  id BIGSERIAL PRIMARY KEY,
  app_id UUID NOT NULL REFERENCES docker_apps(id) ON DELETE CASCADE,
  tps DECIMAL(5,1),
  player_count INT DEFAULT 0,
  memory_used_mb DECIMAL(10,2),
  memory_total_mb DECIMAL(10,2),
  cpu_percent DECIMAL(5,2),
  world_size_mb DECIMAL(10,2),
  lag_spike BOOLEAN DEFAULT FALSE,
  recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_server_metrics_app_time ON server_metrics(app_id, recorded_at DESC);

-- Access Logs (SSH login attempts, console access)
CREATE TABLE IF NOT EXISTS access_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  action VARCHAR(100) NOT NULL,
  source_ip VARCHAR(45),
  status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failed', 'pending')),
  details TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_access_logs_user ON access_logs(user_id, created_at DESC);

-- Config Versions
CREATE TABLE IF NOT EXISTS config_versions (
  id BIGSERIAL PRIMARY KEY,
  app_id UUID NOT NULL REFERENCES docker_apps(id) ON DELETE CASCADE,
  version INT NOT NULL DEFAULT 1,
  config_snapshot JSONB NOT NULL,
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  change_summary TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(app_id, version)
);

-- Maintenance Windows
CREATE TABLE IF NOT EXISTS maintenance_windows (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  app_id UUID REFERENCES docker_apps(id) ON DELETE CASCADE,
  starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
  ends_at TIMESTAMP WITH TIME ZONE NOT NULL,
  status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'active', 'completed', 'cancelled')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Backup Jobs
CREATE TABLE IF NOT EXISTS backup_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  app_id UUID NOT NULL REFERENCES docker_apps(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  schedule_type VARCHAR(20) DEFAULT 'manual' CHECK (schedule_type IN ('manual', 'hourly', 'daily', 'weekly')),
  retention_count INT DEFAULT 7,
  next_run TIMESTAMP WITH TIME ZONE,
  last_run TIMESTAMP WITH TIME ZONE,
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'archived')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Backup Status History
CREATE TABLE IF NOT EXISTS backup_status (
  id BIGSERIAL PRIMARY KEY,
  backup_job_id UUID NOT NULL REFERENCES backup_jobs(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL CHECK (status IN ('running', 'success', 'failed')),
  size_mb DECIMAL(10,2),
  error_message TEXT,
  started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP WITH TIME ZONE
);

-- Alert Configurations
CREATE TABLE IF NOT EXISTS alert_configs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  metric_type VARCHAR(50) NOT NULL,
  operator VARCHAR(10) NOT NULL CHECK (operator IN ('gt', 'lt', 'gte', 'lte', 'eq')),
  threshold DECIMAL(10,2) NOT NULL,
  enabled BOOLEAN DEFAULT TRUE,
  notify_email BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert History
CREATE TABLE IF NOT EXISTS alert_history (
  id BIGSERIAL PRIMARY KEY,
  alert_config_id UUID REFERENCES alert_configs(id) ON DELETE CASCADE,
  metric_type VARCHAR(50) NOT NULL,
  metric_value DECIMAL(10,2) NOT NULL,
  threshold DECIMAL(10,2) NOT NULL,
  operator VARCHAR(10) NOT NULL,
  triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  acknowledged BOOLEAN DEFAULT FALSE
);

-- Health Checks
CREATE TABLE IF NOT EXISTS health_checks (
  id BIGSERIAL PRIMARY KEY,
  app_id UUID NOT NULL REFERENCES docker_apps(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'degraded', 'down', 'unknown')),
  response_time_ms DECIMAL(10,2),
  details JSONB,
  checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_health_checks_app ON health_checks(app_id, checked_at DESC);
