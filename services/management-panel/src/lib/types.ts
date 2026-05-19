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
