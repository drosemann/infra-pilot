import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import crypto from 'crypto';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGINS_FILE = path.join(__dirname, 'plugins.json');

export interface PluginEntry {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  tags: string[];
  downloads: number;
  iconUrl?: string;
  homepage?: string;
  createdAt: string;
  updatedAt: string;
}

export interface PluginInstallation {
  pluginId: string;
  appId: string;
  userId: string;
  installedVersion: string;
  installedAt: string;
}

async function ensureFile(): Promise<void> {
  try {
    await fs.access(PLUGINS_FILE);
  } catch {
    const defaults: { plugins: PluginEntry[]; installations: PluginInstallation[] } = {
      plugins: [
        {
          id: crypto.randomUUID(),
          name: 'Performance Booster',
          description: 'Optimizes JVM and server settings for maximum performance. Includes G1GC tuning, heap optimization, and CPU pinning.',
          version: '1.2.0',
          author: 'Infra Pilot',
          category: 'performance',
          tags: ['jvm', 'gc', 'optimization', 'tuning'],
          downloads: 1240,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 60 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          name: 'Security Hardener',
          description: 'Applies security best-practices: firewall rules, fail2ban config, SSH hardening, and automatic security updates.',
          version: '0.9.1',
          author: 'Infra Pilot',
          category: 'security',
          tags: ['security', 'firewall', 'hardening', 'ssh'],
          downloads: 980,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 45 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          name: 'Backup Automator',
          description: 'Automated backup scheduling with configurable retention, S3/Glacier support, and restore testing.',
          version: '2.0.0',
          author: 'Infra Pilot',
          category: 'backup',
          tags: ['backup', 's3', 'glacier', 'restore', 'cron'],
          downloads: 2150,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 90 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          name: 'Monitoring Stack',
          description: 'One-click Prometheus + Grafana setup with pre-built dashboards for JVM, Docker, and system metrics.',
          version: '1.5.0',
          author: 'Infra Pilot',
          category: 'monitoring',
          tags: ['prometheus', 'grafana', 'metrics', 'dashboard'],
          downloads: 1890,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 30 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          name: 'Log Shipper',
          description: 'Centralized log shipping to Elasticsearch, Loki, or any syslog destination with structured parsing.',
          version: '1.0.0',
          author: 'Infra Pilot',
          category: 'logging',
          tags: ['logs', 'elasticsearch', 'loki', 'syslog', 'parsing'],
          downloads: 760,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 20 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          name: 'Auto Scaler',
          description: 'Automatically scales containers based on CPU, memory, or custom metrics thresholds.',
          version: '0.8.0',
          author: 'Infra Pilot',
          category: 'scaling',
          tags: ['scaling', 'auto-scale', 'metrics', 'thresholds'],
          downloads: 540,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 15 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          name: 'Config Sync',
          description: 'Synchronizes configuration files across multiple containers with Git-backed version control.',
          version: '1.1.0',
          author: 'Infra Pilot',
          category: 'configuration',
          tags: ['config', 'sync', 'git', 'version-control'],
          downloads: 430,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 10 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
        {
          id: crypto.randomUUID(),
          name: 'Webhook Gateway',
          description: 'Custom webhook receiver with filtering, transformation, and routing to containers.',
          version: '0.5.0',
          author: 'Infra Pilot',
          category: 'integration',
          tags: ['webhook', 'api', 'routing', 'transformation'],
          downloads: 320,
          iconUrl: '',
          homepage: '',
          createdAt: new Date(Date.now() - 5 * 86400000).toISOString(),
          updatedAt: new Date().toISOString(),
        },
      ],
      installations: [],
    };
    await fs.writeFile(PLUGINS_FILE, JSON.stringify(defaults, null, 2));
  }
}

async function getData(): Promise<{ plugins: PluginEntry[]; installations: PluginInstallation[] }> {
  await ensureFile();
  const raw = await fs.readFile(PLUGINS_FILE, 'utf8');
  return JSON.parse(raw);
}

async function saveData(data: { plugins: PluginEntry[]; installations: PluginInstallation[] }): Promise<void> {
  await fs.writeFile(PLUGINS_FILE, JSON.stringify(data, null, 2));
}

export async function listPlugins(userId?: string, appId?: string): Promise<any[]> {
  const data = await getData();
  return data.plugins.map(p => {
    const inst = data.installations.find(i => i.pluginId === p.id && (!appId || i.appId === appId));
    return {
      ...p,
      installed: !!inst,
      installedVersion: inst?.installedVersion,
      installedAt: inst?.installedAt,
      appId: inst?.appId,
    };
  });
}

export async function getPlugin(id: string, userId?: string, appId?: string): Promise<any | null> {
  const data = await getData();
  const plugin = data.plugins.find(p => p.id === id);
  if (!plugin) return null;
  const inst = data.installations.find(i => i.pluginId === id && (!appId || i.appId === appId));
  return {
    ...plugin,
    installed: !!inst,
    installedVersion: inst?.installedVersion,
    installedAt: inst?.installedAt,
    appId: inst?.appId,
  };
}

export async function installPlugin(pluginId: string, appId: string, userId: string): Promise<void> {
  const data = await getData();
  const plugin = data.plugins.find(p => p.id === pluginId);
  if (!plugin) throw new Error('Plugin not found');
  const existing = data.installations.find(i => i.pluginId === pluginId && i.appId === appId);
  if (existing) return;
  data.installations.push({
    pluginId,
    appId,
    userId,
    installedVersion: plugin.version,
    installedAt: new Date().toISOString(),
  });
  plugin.downloads++;
  await saveData(data);
}

export async function uninstallPlugin(pluginId: string, appId: string): Promise<void> {
  const data = await getData();
  data.installations = data.installations.filter(i => !(i.pluginId === pluginId && i.appId === appId));
  await saveData(data);
}

export async function publishPlugin(entry: PluginEntry): Promise<PluginEntry> {
  const data = await getData();
  data.plugins.push(entry);
  await saveData(data);
  return entry;
}
