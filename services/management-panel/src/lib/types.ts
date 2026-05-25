import { createContext, useContext } from 'react';

export type SetupMode = 'personal' | 'business';

export interface SetupStatus {
  initialized: boolean;
  mode: SetupMode | null;
}

export interface DockerApp {
  id: string;
  user_id: string;
  name: string;
  image: string;
  status: 'running' | 'stopped' | 'restarting' | 'error';
  container_id?: string;
  ports?: Array<{ hostPort: number; containerPort: number; protocol: string }>;
  environment_vars?: Record<string, string>;
  volumes?: Array<{ hostPath: string; containerPath: string }>;
  restart_policy?: string;
  memory_limit?: string;
  cpu_shares?: number;
  description?: string;
  labels?: Record<string, string>;
  created_at: string;
  updated_at: string;
  started_at?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  role: 'admin' | 'user';
  mode_at_signup: SetupMode;
}

export interface AppConfig {
  mode: SetupMode;
}

export interface Customer {
  id: string;
  owner_user_id: string;
  name: string;
  email?: string;
  created_at?: string;
  updated_at?: string;
}

// Feature gates based on mode
export const featureGates = {
  isPersonal: (mode: SetupMode) => mode === 'personal',
  isBusiness: (mode: SetupMode) => mode === 'business',
  
  // Personal mode features (always available)
  canManageLocalApps: (mode: SetupMode) => true,
  canViewLogs: (mode: SetupMode) => true,
  canConfigureEnv: (mode: SetupMode) => true,
  
  // Business mode features
  canManageCustomers: (mode: SetupMode) => mode === 'business',
  canManagePlans: (mode: SetupMode) => mode === 'business',
  canViewBilling: (mode: SetupMode) => mode === 'business',
  canWhitelabel: (mode: SetupMode) => mode === 'business',
  canManageTeam: (mode: SetupMode) => mode === 'business',
  canViewAuditLogs: (mode: SetupMode) => mode === 'business',
  canConfigureHosting: (mode: SetupMode) => mode === 'business',
};

// Config context for global access to mode
export const ConfigContext = createContext<{ mode: SetupMode; loading: boolean }>({
  mode: 'personal',
  loading: true,
});

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within ConfigProvider');
  }
  return context;
};


export interface ServerPreset {
  id: string;
  name: string;
  description: string;
  image: string;
  startupCommand: string;
  resources: {
    ram: string;
    cpu: number;
    disk: string;
  };
  ports: Array<{ hostPort: number; containerPort: number; protocol: 'tcp' | 'udp' }>;
  environmentVars: Record<string, string>;
}

// ============================================================================
// Phase 4 Types
// ============================================================================

export interface ServerMetric {
  id: number;
  app_id: string;
  tps: number | null;
  player_count: number;
  memory_used_mb: number;
  memory_total_mb: number;
  cpu_percent: number;
  world_size_mb: number;
  lag_spike: boolean;
  recorded_at: string;
}

export interface AccessLog {
  id: number;
  user_id: string;
  action: string;
  source_ip: string;
  status: 'success' | 'failed' | 'pending';
  details: string;
  created_at: string;
}

export interface ConfigVersion {
  id: number;
  app_id: string;
  version: number;
  config_snapshot: Record<string, any>;
  created_by: string;
  change_summary: string;
  created_at: string;
}

export interface MaintenanceWindow {
  id: string;
  user_id: string;
  title: string;
  description: string;
  app_id: string;
  starts_at: string;
  ends_at: string;
  status: 'scheduled' | 'active' | 'completed' | 'cancelled';
  created_at: string;
}

export interface BackupJob {
  id: string;
  user_id: string;
  app_id: string;
  name: string;
  schedule_type: 'manual' | 'hourly' | 'daily' | 'weekly';
  retention_count: number;
  next_run: string;
  last_run: string;
  status: 'active' | 'paused' | 'archived';
  created_at: string;
}

export interface BackupStatusEntry {
  id: number;
  backup_job_id: string;
  status: 'running' | 'success' | 'failed';
  size_mb: number;
  error_message: string;
  started_at: string;
  completed_at: string;
}

export interface AlertConfig {
  id: string;
  user_id: string;
  metric_type: string;
  operator: 'gt' | 'lt' | 'gte' | 'lte' | 'eq';
  threshold: number;
  enabled: boolean;
  notify_email: boolean;
  created_at: string;
}

export interface AlertHistoryEntry {
  id: number;
  alert_config_id: string;
  metric_type: string;
  metric_value: number;
  threshold: number;
  operator: string;
  triggered_at: string;
  acknowledged: boolean;
}

export interface HealthCheck {
  id: number;
  app_id: string;
  status: 'healthy' | 'degraded' | 'down' | 'unknown';
  response_time_ms: number;
  details: Record<string, any>;
  checked_at: string;
}
