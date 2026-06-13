import { promises as fs } from 'fs';
import path from 'path';
import { createClient } from '@supabase/supabase-js';

const DASHBOARDS_FILE = path.resolve(process.cwd(), 'data', 'dashboards.json');

export type PanelType = 'time-series' | 'stat' | 'log-list' | 'alert-list';

export interface PanelDataSource {
  type: 'metrics' | 'logs' | 'alerts' | 'backups' | 'apps';
  query?: string;
  aggregation?: string;
  period?: string;
}

export interface DashboardPanel {
  id: string;
  type: PanelType;
  title: string;
  dataSource: PanelDataSource;
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, any>;
}

export interface DashboardDefinition {
  id: string;
  name: string;
  description?: string;
  panels: DashboardPanel[];
  layout: { columns: number; rowHeight: number };
  refreshInterval: number;
  starred: boolean;
  created_at: string;
  updated_at: string;
}

let supabaseUrl = process.env.VITE_SUPABASE_URL || 'http://localhost:54321';
let supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'test-anon-key';
let supabase = createClient(supabaseUrl, supabaseKey);

export function setSupabase(client: ReturnType<typeof createClient>) {
  supabase = client;
}

async function ensureFile() {
  await fs.mkdir(path.dirname(DASHBOARDS_FILE), { recursive: true });
  try {
    await fs.access(DASHBOARDS_FILE);
  } catch {
    await fs.writeFile(DASHBOARDS_FILE, '[]', 'utf-8');
  }
}

async function readDashboards(): Promise<DashboardDefinition[]> {
  await ensureFile();
  try {
    const raw = await fs.readFile(DASHBOARDS_FILE, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function writeDashboards(dashboards: DashboardDefinition[]): Promise<void> {
  await ensureFile();
  await fs.writeFile(DASHBOARDS_FILE, JSON.stringify(dashboards, null, 2), 'utf-8');
}

export async function listDashboards(): Promise<DashboardDefinition[]> {
  return readDashboards();
}

export async function getDashboard(id: string): Promise<DashboardDefinition | null> {
  const dashboards = await readDashboards();
  return dashboards.find(d => d.id === id) || null;
}

export async function createDashboard(data: Partial<DashboardDefinition>): Promise<DashboardDefinition> {
  const dashboards = await readDashboards();
  const now = new Date().toISOString();
  const dashboard: DashboardDefinition = {
    id: data.id || crypto.randomUUID(),
    name: data.name || 'New Dashboard',
    description: data.description,
    panels: data.panels || [],
    layout: data.layout || { columns: 12, rowHeight: 100 },
    refreshInterval: data.refreshInterval || 30,
    starred: data.starred || false,
    created_at: now,
    updated_at: now,
  };
  dashboards.push(dashboard);
  await writeDashboards(dashboards);
  return dashboard;
}

export async function updateDashboard(id: string, data: Partial<DashboardDefinition>): Promise<DashboardDefinition | null> {
  const dashboards = await readDashboards();
  const idx = dashboards.findIndex(d => d.id === id);
  if (idx < 0) return null;
  dashboards[idx] = {
    ...dashboards[idx],
    ...data,
    id,
    updated_at: new Date().toISOString(),
  };
  await writeDashboards(dashboards);
  return dashboards[idx];
}

export async function deleteDashboard(id: string): Promise<boolean> {
  const dashboards = await readDashboards();
  const idx = dashboards.findIndex(d => d.id === id);
  if (idx < 0) return false;
  dashboards.splice(idx, 1);
  await writeDashboards(dashboards);
  return true;
}

export async function getDashboardData(id: string, params?: { period?: string }): Promise<any> {
  const dashboard = await getDashboard(id);
  if (!dashboard) throw new Error('Dashboard not found');

  const period = params?.period || '1h';
  const results: Record<string, any> = {};

  for (const panel of dashboard.panels) {
    try {
      results[panel.id] = await resolvePanelData(panel, period);
    } catch (err) {
      results[panel.id] = { error: (err as Error).message };
    }
  }

  return { dashboard: dashboard.name, period, panels: results };
}

async function resolvePanelData(panel: DashboardPanel, period: string): Promise<any> {
  const ds = panel.dataSource;

  switch (ds.type) {
    case 'metrics': {
      const since = getPeriodMs(period);
      const { data } = await supabase
        .from('server_metrics')
        .select('recorded_at, cpu_percent, memory_used_mb, memory_total_mb, tps, player_count')
        .gte('recorded_at', new Date(Date.now() - since).toISOString())
        .order('recorded_at', { ascending: true })
        .limit(500);
      return { data: data || [], source: 'server_metrics' };
    }
    case 'logs': {
      const since = getPeriodMs(period);
      const { data } = await supabase
        .from('app_logs')
        .select('*')
        .gte('created_at', new Date(Date.now() - since).toISOString())
        .order('created_at', { ascending: false })
        .limit(100);
      return { data: data || [], source: 'app_logs' };
    }
    case 'alerts': {
      const since = getPeriodMs(period);
      const { data } = await supabase
        .from('alert_history')
        .select('*')
        .gte('triggered_at', new Date(Date.now() - since).toISOString())
        .order('triggered_at', { ascending: false })
        .limit(100);
      return { data: data || [], source: 'alert_history' };
    }
    case 'backups': {
      const since = getPeriodMs(period);
      const { data } = await supabase
        .from('backup_status')
        .select('*')
        .gte('started_at', new Date(Date.now() - since).toISOString())
        .order('started_at', { ascending: false })
        .limit(100);
      return { data: data || [], source: 'backup_status' };
    }
    case 'apps': {
      const { data } = await supabase
        .from('docker_apps')
        .select('*')
        .order('created_at', { ascending: false });
      return { data: data || [], source: 'docker_apps' };
    }
    default:
      return { data: [], source: ds.type };
  }
}

function getPeriodMs(period: string): number {
  const map: Record<string, number> = {
    '5m': 300000,
    '15m': 900000,
    '30m': 1800000,
    '1h': 3600000,
    '6h': 21600000,
    '24h': 86400000,
    '7d': 604800000,
    '30d': 2592000000,
  };
  return map[period] || 3600000;
}
