import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:3001';

class APIClient {
  private api: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: { 'Content-Type': 'application/json' },
      timeout: 15000,
    });

    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.token = null;
          await SecureStore.deleteItemAsync('auth_token');
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearToken() {
    this.token = null;
    delete this.api.defaults.headers.common['Authorization'];
  }

  get instance(): AxiosInstance {
    return this.api;
  }

  async get<T>(url: string, params?: Record<string, any>): Promise<T> {
    const res = await this.api.get<T>(url, { params });
    return res.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const res = await this.api.post<T>(url, data);
    return res.data;
  }

  async patch<T>(url: string, data?: any): Promise<T> {
    const res = await this.api.patch<T>(url, data);
    return res.data;
  }

  async delete<T>(url: string): Promise<T> {
    const res = await this.api.delete<T>(url);
    return res.data;
  }
}

export const apiClient = new APIClient();
