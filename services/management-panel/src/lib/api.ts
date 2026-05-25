import axios, { AxiosInstance } from 'axios';
import { DockerApp, SetupStatus, UserProfile, AppConfig, Customer, ServerPreset, ServerMetric, AccessLog, ConfigVersion, MaintenanceWindow, BackupJob, BackupStatusEntry, AlertConfig, AlertHistoryEntry, HealthCheck } from './types';

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:3001';

class APIClient {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  setToken(token: string) {
    this.token = token;
    this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearToken() {
    this.token = null;
    delete this.api.defaults.headers.common['Authorization'];
  }

  // Setup endpoints
  async getSetupStatus(): Promise<SetupStatus> {
    const res = await this.api.get('/api/setup/status');
    return res.data;
  }

  async initSetup(email: string, password: string, displayName: string, mode: 'personal' | 'business') {
    const res = await this.api.post('/api/setup/init', {
      email,
      password,
      displayName,
      mode,
    });
    return res.data;
  }



  async listPresets(): Promise<ServerPreset[]> {
    const res = await this.api.get('/api/presets');
    return res.data;
  }

  // Docker app endpoints
  async listApps(): Promise<DockerApp[]> {
    const res = await this.api.get('/api/apps');
    return res.data;
  }

  async getApp(appId: string): Promise<DockerApp> {
    const res = await this.api.get(`/api/apps/${appId}`);
    return res.data;
  }

  async createApp(app: Partial<DockerApp>): Promise<DockerApp> {
    const res = await this.api.post('/api/apps', app);
    return res.data;
  }

  async updateApp(appId: string, updates: Partial<DockerApp>): Promise<DockerApp> {
    const res = await this.api.patch(`/api/apps/${appId}`, updates);
    return res.data;
  }

  async deleteApp(appId: string): Promise<void> {
    await this.api.delete(`/api/apps/${appId}`);
  }

  // Container control endpoints
  async startApp(appId: string): Promise<DockerApp> {
    const res = await this.api.post(`/api/apps/${appId}/start`);
    return res.data;
  }

  async stopApp(appId: string): Promise<DockerApp> {
    const res = await this.api.post(`/api/apps/${appId}/stop`);
    return res.data;
  }

  async restartApp(appId: string): Promise<DockerApp> {
    const res = await this.api.post(`/api/apps/${appId}/restart`);
    return res.data;
  }

  async getLogs(appId: string, limit = 50, offset = 0): Promise<Array<any>> {
    const res = await this.api.get(`/api/apps/${appId}/logs`, {
      params: { limit, offset },
    });
    return res.data;
  }

  // User endpoints
  async getUser(): Promise<UserProfile> {
    const res = await this.api.get('/api/user');
    return res.data;
  }

  // Config endpoints
  async getConfig(): Promise<AppConfig> {
    const res = await this.api.get('/api/config/mode');
    return res.data;
  }

  // Customers (Business Mode MVP)
  async getCustomers(): Promise<Customer[]> {
    const res = await this.api.get('/api/customers');
    return res.data;
  }

  async createCustomer(customer: Partial<Customer>): Promise<Customer> {
    const res = await this.api.post('/api/customers', customer);
    return res.data;
  }

  async updateCustomer(customerId: string, updates: Partial<Customer>): Promise<any> {
    const res = await this.api.patch(`/api/customers/${customerId}`, updates);
    return res.data;
  }

  async deleteCustomer(customerId: string): Promise<any> {
    const res = await this.api.delete(`/api/customers/${customerId}`);
    return res.data;
  }

  // Seed demo data (customers + apps)
  async seedDemo(): Promise<any> {
    const res = await this.api.post('/api/seed-demo');
    return res.data;
  }

  // Phase 4: Server Metrics
  async getServerMetrics(appId: string, range = '30m'): Promise<ServerMetric[]> {
    const res = await this.api.get(`/api/apps/${appId}/metrics`, { params: { range } });
    return res.data;
  }

  async getAggregatedMetrics(): Promise<any> {
    const res = await this.api.get('/api/metrics/aggregated');
    return res.data;
  }

  // Access Logs
  async getAccessLogs(limit = 50, offset = 0): Promise<AccessLog[]> {
    const res = await this.api.get('/api/logs/access', { params: { limit, offset } });
    return res.data;
  }

  // Config Versions
  async getConfigVersions(appId: string): Promise<ConfigVersion[]> {
    const res = await this.api.get(`/api/apps/${appId}/config-versions`);
    return res.data;
  }

  async createConfigVersion(appId: string, snapshot: Record<string, any>, summary: string): Promise<ConfigVersion> {
    const res = await this.api.post(`/api/apps/${appId}/config-versions`, { config_snapshot: snapshot, change_summary: summary });
    return res.data;
  }

  async rollbackConfig(appId: string, version: number): Promise<ConfigVersion> {
    const res = await this.api.post(`/api/apps/${appId}/config-versions/${version}/rollback`);
    return res.data;
  }

  // Maintenance Windows
  async getMaintenanceWindows(): Promise<MaintenanceWindow[]> {
    const res = await this.api.get('/api/maintenance-windows');
    return res.data;
  }

  async createMaintenanceWindow(window: Partial<MaintenanceWindow>): Promise<MaintenanceWindow> {
    const res = await this.api.post('/api/maintenance-windows', window);
    return res.data;
  }

  async updateMaintenanceWindow(id: string, updates: Partial<MaintenanceWindow>): Promise<MaintenanceWindow> {
    const res = await this.api.patch(`/api/maintenance-windows/${id}`, updates);
    return res.data;
  }

  // Backup Jobs
  async getBackupJobs(): Promise<BackupJob[]> {
    const res = await this.api.get('/api/backup-jobs');
    return res.data;
  }

  async createBackupJob(job: Partial<BackupJob>): Promise<BackupJob> {
    const res = await this.api.post('/api/backup-jobs', job);
    return res.data;
  }

  async updateBackupJob(id: string, updates: Partial<BackupJob>): Promise<BackupJob> {
    const res = await this.api.patch(`/api/backup-jobs/${id}`, updates);
    return res.data;
  }

  async deleteBackupJob(id: string): Promise<void> {
    await this.api.delete(`/api/backup-jobs/${id}`);
  }

  async getBackupStatus(jobId: string): Promise<BackupStatusEntry[]> {
    const res = await this.api.get(`/api/backup-jobs/${jobId}/status`);
    return res.data;
  }

  // Alert Configs
  async getAlertConfigs(): Promise<AlertConfig[]> {
    const res = await this.api.get('/api/alert-configs');
    return res.data;
  }

  async createAlertConfig(config: Partial<AlertConfig>): Promise<AlertConfig> {
    const res = await this.api.post('/api/alert-configs', config);
    return res.data;
  }

  async updateAlertConfig(id: string, updates: Partial<AlertConfig>): Promise<AlertConfig> {
    const res = await this.api.patch(`/api/alert-configs/${id}`, updates);
    return res.data;
  }

  async deleteAlertConfig(id: string): Promise<void> {
    await this.api.delete(`/api/alert-configs/${id}`);
  }

  async getAlertHistory(): Promise<AlertHistoryEntry[]> {
    const res = await this.api.get('/api/alert-history');
    return res.data;
  }

  async acknowledgeAlert(id: number): Promise<void> {
    await this.api.post(`/api/alert-history/${id}/acknowledge`);
  }

  // Health Checks
  async getHealthChecks(appId?: string): Promise<HealthCheck[]> {
    const params = appId ? { app_id: appId } : {};
    const res = await this.api.get('/api/health-checks', { params });
    return res.data;
  }

  async getReports(startDate?: string, endDate?: string): Promise<any> {
    const params: any = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await this.api.get('/api/reports', { params });
    return res.data;
  }

  async exportReport(format: 'pdf' | 'csv', startDate?: string, endDate?: string): Promise<Blob> {
    const params: any = { format };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    const res = await this.api.get('/api/reports/export', { params, responseType: 'blob' });
    return res.data;
  }

  // Health check
  async health(): Promise<{ status: string }> {
    const res = await this.api.get('/health');
    return res.data;
  }
}

export const apiClient = new APIClient();
