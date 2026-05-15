import axios, { AxiosInstance } from 'axios';
import { DockerApp, SetupStatus, UserProfile, AppConfig, Customer } from './types';

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

  // Health check
  async health(): Promise<{ status: string }> {
    const res = await this.api.get('/health');
    return res.data;
  }
}

export const apiClient = new APIClient();
