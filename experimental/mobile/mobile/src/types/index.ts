export interface Server {
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
  javaVersion?: string;
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
}

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

export interface BillingInfo {
  balance: number;
  totalSpent: number;
  totalToppedUp: number;
}

export interface Transaction {
  id: string;
  amount: number;
  description: string;
  type: 'topup' | 'charge' | 'refund' | 'bonus';
  balanceAfter: number;
  timestamp: string;
}

export interface CostEstimate {
  hourly: number;
  daily: number;
  monthly: number;
}

export interface LogEntry {
  timestamp: string;
  message: string;
  level: 'info' | 'warn' | 'error' | 'debug';
}

export interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}
