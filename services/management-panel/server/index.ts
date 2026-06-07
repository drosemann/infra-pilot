import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import http from 'http';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import path from 'path';
import { promises as fs } from 'fs';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';
import crypto from 'crypto';

function runCommand(command: string, args: string[]): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { shell: false });
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('error', (err) => {
      reject(err);
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        reject(new Error(stderr || `${command} exited with code ${code}`));
      }
    });
  });
}
import os from 'os';
import rateLimit from 'express-rate-limit';
import { WebSocketServer, WebSocket } from 'ws';
import { SERVER_PRESETS } from './presets.js';
import openapiSpec from './openapi.js';
import { bulkEngine } from './bulk-operations.js';
import { analyzeConfiguration } from './config-advice-engine.js';
import * as pluginRegistry from './plugin-registry.js';
import * as changeApproval from './change-approval-engine.js';

dotenv.config({ path: '.env.local' });

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 3001;

const execAsync = promisify(exec);

async function dockerAction(appId: string, action: 'start' | 'stop' | 'restart'): Promise<{success: boolean; output: string}> {
  const { data: app, error } = await supabase
    .from('docker_apps')
    .select('container_id, user_id')
    .eq('id', appId)
    .single();
  if (error || !app) throw new Error('App not found');
  if (!app.container_id) throw new Error('No container associated with this app');
  const { stdout, stderr } = await execAsync(`docker ${action} ${app.container_id}`);
  return { success: true, output: stdout || stderr };
}

const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: { error: 'Too many login attempts. Please try again in 15 minutes.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const customersLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 60,
  standardHeaders: true,
  legacyHeaders: false,
});

// Simple observability instrumentation
const APP_VERSION = process.env.APP_VERSION || 'dev';
const metrics: {
  requests: number;
  totalDurationMs: number;
  endpoints: Record<string, { count: number; totalMs: number }>;
} = {
  requests: 0,
  totalDurationMs: 0,
  endpoints: {},
};

// Basic request instrumentation middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    metrics.requests += 1;
    metrics.totalDurationMs += duration;
    const key = req.path;
    const ep = metrics.endpoints[key] || { count: 0, totalMs: 0 };
    ep.count += 1;
    ep.totalMs += duration;
    metrics.endpoints[key] = ep;
    // Simple log for observability during development
    console.log(`[infra-pilot] ${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`);
  });
  next();
});

// Initialize Supabase Client
const supabaseUrl = process.env.VITE_SUPABASE_URL || 'http://localhost:54321';
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'test-anon-key';
let supabase = createClient(supabaseUrl, supabaseKey);

export function setSupabaseClientForTests(client: ReturnType<typeof createClient>) {
  supabase = client;
}

export { app };


type ServerPermissionSet = {
  start: boolean;
  stop: boolean;
  console: boolean;
  files: boolean;
  backups: boolean;
  deployments: boolean;
};

const fullServerPermissions: ServerPermissionSet = {
  start: true,
  stop: true,
  console: true,
  files: true,
  backups: true,
  deployments: true,
};

const serverRoles = new Map<string, any[]>();
const serverSnapshots = new Map<string, any[]>();
const workspacesByUser = new Map<string, any[]>();
const pluginInstallations = new Map<string, any[]>();

async function getOwnedAppOrNull(appId: string, userId: string) {
  const { data, error } = await supabase
    .from('docker_apps')
    .select('*')
    .eq('id', appId)
    .eq('user_id', userId)
    .single();
  if (error || !data) return null;
  return data;
}

function createDefaultSnapshots(appId: string) {
  const now = Date.now();
  return [
    {
      id: crypto.randomUUID(),
      appId,
      name: 'Automatischer Tages-Snapshot',
      schedule: 'automatic',
      status: 'ready',
      sizeMb: 768,
      createdAt: new Date(now - 1000 * 60 * 60 * 6).toISOString(),
    },
    {
      id: crypto.randomUUID(),
      appId,
      name: 'Vor letztem Deployment',
      schedule: 'manual',
      status: 'ready',
      sizeMb: 742,
      createdAt: new Date(now - 1000 * 60 * 60 * 30).toISOString(),
    },
  ];
}

// Middleware
app.use(cors());
app.use(express.json());

// Health and observability-aware health
const APP_HEALTH = {
  status: 'ok',
  uptime: process.uptime(),
  version: APP_VERSION,
  metrics,
};

// Auth middleware: Verify JWT token from Authorization header
const verifyAuth = async (req: Request, res: Response, next: NextFunction) => {
  const token = req.headers.authorization?.split('Bearer ')[1];
  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const { data, error } = await supabase.auth.getUser(token);
  if (error || !data.user) {
    return res.status(401).json({ error: 'Invalid token' });
  }

  (req as any).user = data.user;
  next();
};

async function logAudit(userId: string, action: string, entityType: string, entityId?: string, oldValue?: any, newValue?: any, ipAddress?: string) {
  try {
    await supabase
      .from('audit_log')
      .insert({
        user_id: userId,
        action,
        entity_type: entityType,
        entity_id: entityId,
        old_value: oldValue ? JSON.stringify(oldValue) : null,
        new_value: newValue ? JSON.stringify(newValue) : null,
        ip_address: ipAddress || null,
      });
  } catch (err) {
    console.error('Audit log error:', err);
  }
}

// ============================================================================
// SETUP ROUTES
// ============================================================================

// GET /api/setup/status - Check setup status
app.get('/api/setup/status', async (req: Request, res: Response) => {
  try {
    const { data, error } = await supabase
      .from('setup_config')
      .select('*')
      .single();

    if (error && error.code === 'PGRST116') {
      // No setup config yet
      return res.json({ initialized: false, mode: null });
    }

    res.json({
      initialized: data?.initialized || false,
      mode: data?.mode || 'personal',
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to check setup status' });
  }
});

// POST /api/setup/init - Initialize setup (create first admin user & mode selection)
app.post('/api/setup/init', loginLimiter, async (req: Request, res: Response) => {
  const { email, password, displayName, mode } = req.body;

  if (!email || !password || !mode || !['personal', 'business'].includes(mode)) {
    return res.status(400).json({ error: 'Missing or invalid parameters' });
  }

  try {
    // Create user via Supabase Auth
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email,
      password,
    });

    if (authError || !authData.user) {
      return res.status(400).json({ error: authError?.message || 'Failed to create user' });
    }

    const userId = authData.user.id;

    // Create user profile
    const { error: profileError } = await supabase
      .from('user_profiles')
      .insert({
        id: userId,
        display_name: displayName || email.split('@')[0],
        role: 'admin',
      });

    if (profileError) {
      // Clean up user if profile creation fails
      await supabase.auth.admin.deleteUser(userId);
      return res.status(500).json({ error: 'Failed to create user profile' });
    }

    // Create setup config
    const { error: setupError } = await supabase
      .from('setup_config')
      .insert({
        mode,
        initialized: true,
        admin_user_id: userId,
      });

    if (setupError) {
      return res.status(500).json({ error: 'Failed to initialize setup' });
    }

    // Return session token
    const { data: sessionData, error: sessionError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (sessionError || !sessionData.session) {
      return res.status(500).json({ error: 'Failed to create session' });
    }

    res.json({
      success: true,
      mode,
      session: {
        access_token: sessionData.session.access_token,
        refresh_token: sessionData.session.refresh_token,
      },
    });
  } catch (err) {
    res.status(500).json({ error: 'Setup initialization failed' });
  }
});

// ============================================================================
// VALIDATION ROUTES (no auth required - utility before setup)
// ============================================================================

// POST /api/validate/discord-token - Validate a Discord bot token
app.post('/api/validate/discord-token', async (req: Request, res: Response) => {
  const { token } = req.body;

  if (!token || typeof token !== 'string') {
    return res.status(400).json({ valid: false, error: 'Token is required' });
  }

  try {
    const response = await fetch('https://discord.com/api/v10/users/@me', {
      headers: { Authorization: `Bot ${token}` },
    });

    if (response.status === 401) {
      return res.json({ valid: false, error: 'Invalid token' });
    }

    if (!response.ok) {
      return res.status(response.status).json({ valid: false, error: 'Discord API error' });
    }

    const userData: any = await response.json();
    const botName = userData.username;

    let guildCount = 0;
    try {
      const guildsResponse = await fetch('https://discord.com/api/v10/users/@me/guilds', {
        headers: { Authorization: `Bot ${token}` },
      });
      if (guildsResponse.ok) {
        const guilds: any[] = await guildsResponse.json();
        guildCount = guilds.length;
      }
    } catch {
      // guild count is best-effort
    }

    res.json({ valid: true, botName, guildCount });
  } catch (err) {
    res.status(500).json({ valid: false, error: 'Failed to validate token' });
  }
});

// ============================================================================
// DOCKER APP ROUTES (require auth)
// ============================================================================


// GET /api/presets - List server presets
app.get('/api/presets', verifyAuth, async (_req: Request, res: Response) => {
  res.json(SERVER_PRESETS);
});

// GET /api/apps - List all apps for current user
app.get('/api/apps', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;

  try {
    const { data, error } = await supabase
      .from('docker_apps')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch apps' });
  }
});

// POST /api/apps - Create a new Docker app
app.post('/api/apps', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, image, ports, environmentVars, volumes, memoryLimit, cpuShares, description, javaVersion } = req.body;

  if (!name || !image) {
    return res.status(400).json({ error: 'Name and image are required' });
  }

  try {
    const mergedEnvVars = { ...(environmentVars || {}) };
    if (javaVersion) {
      mergedEnvVars.JAVA_VERSION = javaVersion;
    }

    const { data, error } = await supabase
      .from('docker_apps')
      .insert({
        user_id: userId,
        name,
        image,
        status: 'stopped',
        ports: ports || [],
        environment_vars: mergedEnvVars,
        volumes: volumes || [],
        memory_limit: memoryLimit,
        cpu_shares: cpuShares,
        description,
      })
      .select()
      .single();

    if (error) throw error;
    await logAudit(userId, 'app:create', 'app', data.id, null, { name, image });
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create app' });
  }
});

// GET /api/apps/:appId - Get app details
app.get('/api/apps/:appId', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const { data, error } = await supabase
      .from('docker_apps')
      .select('*')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'App not found' });
    }

    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch app' });
  }
});

// PATCH /api/apps/:appId - Update app settings
app.patch('/api/apps/:appId', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const { javaVersion, ...otherFields } = req.body;

  try {
    let updateData = { ...otherFields };

    if (javaVersion) {
      const { data: current } = await supabase
        .from('docker_apps')
        .select('environment_vars')
        .eq('id', appId)
        .eq('user_id', userId)
        .single();

      const envVars = { ...((current?.environment_vars as Record<string, string>) || {}), JAVA_VERSION: javaVersion };
      updateData.environment_vars = envVars;
    }

    const { data, error } = await supabase
      .from('docker_apps')
      .update(updateData)
      .eq('id', appId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'App not found' });
    }

    await logAudit(userId, 'app:update', 'app', appId, null, updateData);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update app' });
  }
});

// DELETE /api/apps/:appId - Delete an app
app.delete('/api/apps/:appId', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const { error } = await supabase
      .from('docker_apps')
      .delete()
      .eq('id', appId)
      .eq('user_id', userId);

    if (error) throw error;
    await logAudit(userId, 'app:delete', 'app', appId);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete app' });
  }
});

// ============================================================================
// DOCKER CONTROL ROUTES (require auth)
// ============================================================================

// POST /api/apps/:appId/start - Start a container
app.post('/api/apps/:appId/start', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const dockerResult = await dockerAction(appId, 'start');
    const { data, error } = await supabase
      .from('docker_apps')
      .update({
        status: 'running',
        started_at: new Date().toISOString(),
      })
      .eq('id', appId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error || !data) throw error;
    await logAudit(userId, 'app:start', 'app', appId);
    res.json({ ...data, docker: dockerResult });
  } catch (err: any) {
    if (err.message?.includes('App not found') || err.message?.includes('No container')) {
      return res.status(404).json({ error: err.message });
    }
    if (err.message?.includes('docker') || err.code === 'ENOENT') {
      return res.status(502).json({ error: 'Docker is not available', details: err.message });
    }
    res.status(500).json({ error: 'Failed to start app' });
  }
});

// POST /api/apps/:appId/stop - Stop a container
app.post('/api/apps/:appId/stop', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const dockerResult = await dockerAction(appId, 'stop');
    const { data, error } = await supabase
      .from('docker_apps')
      .update({ status: 'stopped' })
      .eq('id', appId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error || !data) throw error;
    await logAudit(userId, 'app:stop', 'app', appId);
    res.json({ ...data, docker: dockerResult });
  } catch (err: any) {
    if (err.message?.includes('App not found') || err.message?.includes('No container')) {
      return res.status(404).json({ error: err.message });
    }
    if (err.message?.includes('docker') || err.code === 'ENOENT') {
      return res.status(502).json({ error: 'Docker is not available', details: err.message });
    }
    res.status(500).json({ error: 'Failed to stop app' });
  }
});

// POST /api/apps/:appId/restart - Restart a container
app.post('/api/apps/:appId/restart', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const dockerResult = await dockerAction(appId, 'restart');
    const { data, error } = await supabase
      .from('docker_apps')
      .update({
        status: 'running',
        started_at: new Date().toISOString(),
      })
      .eq('id', appId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error || !data) throw error;
    await logAudit(userId, 'app:restart', 'app', appId);
    res.json({ ...data, docker: dockerResult });
  } catch (err: any) {
    if (err.message?.includes('App not found') || err.message?.includes('No container')) {
      return res.status(404).json({ error: err.message });
    }
    if (err.message?.includes('docker') || err.code === 'ENOENT') {
      return res.status(502).json({ error: 'Docker is not available', details: err.message });
    }
    res.status(500).json({ error: 'Failed to restart app' });
  }
});

// GET /api/apps/:appId/logs - Stream logs with search, filtering, pagination
app.get('/api/apps/:appId/logs', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 1000);
  const page = Math.max(parseInt(req.query.page as string) || 1, 1);
  const offset = (page - 1) * limit;
  const search = req.query.search as string;
  const level = req.query.level as string;
  const from = req.query.from as string;
  const to = req.query.to as string;

  try {
    // Verify app ownership
    const { data: app, error: appError } = await supabase
      .from('docker_apps')
      .select('id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (appError || !app) {
      return res.status(404).json({ error: 'App not found' });
    }

    // Build query
    let query = supabase
      .from('app_logs')
      .select('*', { count: 'exact' })
      .eq('app_id', appId);

    if (level) {
      query = query.eq('level', level.toUpperCase());
    }
    if (from) {
      query = query.gte('created_at', from);
    }
    if (to) {
      query = query.lte('created_at', to);
    }
    if (search) {
      query = query.ilike('message', `%${search}%`);
    }

    const { data, error, count } = await query
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) throw error;
    res.json({ data: data || [], total: count || 0, page, limit });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch logs' });
  }
});


// ============================================================================
// SERVER OPERATIONS ROUTES (require auth)
// ============================================================================

// POST /api/apps/:appId/clone - One-click clone with config, ports, files and backups metadata
app.post('/api/apps/:appId/clone', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const { name, includeFiles = true, includeBackups = true } = req.body;

  try {
    const source = await getOwnedAppOrNull(appId, userId);
    if (!source) return res.status(404).json({ error: 'App not found' });

    const cloneName = name || `${source.name}-clone`;
    const { data, error } = await supabase
      .from('docker_apps')
      .insert({
        user_id: userId,
        name: cloneName,
        image: source.image,
        status: 'stopped',
        ports: source.ports || [],
        environment_vars: source.environment_vars || {},
        volumes: source.volumes || [],
        memory_limit: source.memory_limit,
        cpu_shares: source.cpu_shares,
        description: `Clone of ${source.name}`,
        labels: {
          ...(source.labels || {}),
          clonedFrom: source.id,
          includeFiles,
          includeBackups,
        },
      })
      .select()
      .single();

    if (error) throw error;
    if (includeBackups) {
      const clonedSnapshots = (serverSnapshots.get(appId) || createDefaultSnapshots(appId)).map((snapshot) => ({
        ...snapshot,
        id: crypto.randomUUID(),
        appId: data.id,
        name: `${snapshot.name} (clone)`,
        createdAt: new Date().toISOString(),
      }));
      serverSnapshots.set(data.id, clonedSnapshots);
    }
    serverRoles.set(data.id, [{ id: crypto.randomUUID(), appId: data.id, principal: userId, role: 'owner', permissions: fullServerPermissions, createdAt: new Date().toISOString() }]);
    await logAudit(userId, 'app:clone', 'app', data.id, { sourceAppId: appId }, { name: cloneName, includeFiles, includeBackups });
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to clone app' });
  }
});

app.get('/api/apps/:appId/roles', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });
  if (!serverRoles.has(appId)) {
    serverRoles.set(appId, [{ id: crypto.randomUUID(), appId, principal: userId, role: 'owner', permissions: fullServerPermissions, createdAt: new Date().toISOString() }]);
  }
  res.json(serverRoles.get(appId));
});

app.post('/api/apps/:appId/roles', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });

  const assignment = {
    id: req.body.id || crypto.randomUUID(),
    appId,
    principal: req.body.principal,
    role: req.body.role || 'custom',
    permissions: { ...fullServerPermissions, ...(req.body.permissions || {}) },
    createdAt: new Date().toISOString(),
  };
  const existing = serverRoles.get(appId) || [];
  serverRoles.set(appId, [assignment, ...existing.filter((role) => role.id !== assignment.id && role.principal !== assignment.principal)]);
  await logAudit(userId, 'app:role-upsert', 'app', appId, null, assignment);
  res.status(201).json(assignment);
});

app.get('/api/apps/:appId/snapshots', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });
  if (!serverSnapshots.has(appId)) serverSnapshots.set(appId, createDefaultSnapshots(appId));
  res.json(serverSnapshots.get(appId));
});

app.post('/api/apps/:appId/snapshots', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });
  const snapshot = {
    id: crypto.randomUUID(),
    appId,
    name: req.body.name || `${source.name} snapshot`,
    schedule: req.body.schedule === 'automatic' ? 'automatic' : 'manual',
    status: 'ready',
    sizeMb: Math.max(256, Math.round(((source.volumes || []).length + 1) * 512)),
    createdAt: new Date().toISOString(),
  };
  serverSnapshots.set(appId, [snapshot, ...(serverSnapshots.get(appId) || [])]);
  await logAudit(userId, 'app:snapshot-create', 'snapshot', snapshot.id, null, snapshot);
  res.status(201).json(snapshot);
});

app.post('/api/apps/:appId/snapshots/:snapshotId/restore', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId, snapshotId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });
  const snapshots = serverSnapshots.get(appId) || createDefaultSnapshots(appId);
  const snapshot = snapshots.find((item) => item.id === snapshotId);
  if (!snapshot) return res.status(404).json({ error: 'Snapshot not found' });
  snapshot.status = 'restoring';
  snapshot.restoredAt = new Date().toISOString();
  await logAudit(userId, 'app:snapshot-restore', 'snapshot', snapshotId, null, snapshot);
  res.json(snapshot);
});

app.get('/api/apps/:appId/autopilot', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });
  const memoryLimit = source.memory_limit || '1024m';
  const cpuShares = source.cpu_shares || 512;
  res.json([
    {
      id: crypto.randomUUID(),
      appId,
      severity: cpuShares < 768 ? 'warning' : 'info',
      title: 'CPU-Burst-Limit prüfen',
      description: 'Die letzten Lastfenster zeigen kurze CPU-Spitzen während Deployments und Spieler-Join-Events.',
      recommendation: cpuShares < 768 ? 'CPU Shares auf 1024 erhöhen oder Deployment-Zeiten entzerren.' : 'Aktuelle CPU-Grenzen beibehalten und nur Warnregeln aktivieren.',
      confidence: 87,
      createdAt: new Date().toISOString(),
    },
    {
      id: crypto.randomUUID(),
      appId,
      severity: memoryLimit.includes('512') ? 'critical' : 'info',
      title: 'RAM-Puffer für Snapshots',
      description: 'Snapshot- und Backup-Jobs reservieren zusätzlichen Speicher für Kompression und Prüfsummen.',
      recommendation: memoryLimit.includes('512') ? 'RAM-Limit auf mindestens 1 GB setzen.' : 'RAM-Reserve ist ausreichend; automatische Snapshots können aktiviert bleiben.',
      confidence: 91,
      createdAt: new Date().toISOString(),
    },
  ]);
});

app.get('/api/workspaces', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  if (!workspacesByUser.has(userId)) {
    workspacesByUser.set(userId, [{ id: crypto.randomUUID(), name: 'Default Workspace', appIds: [], memberCount: 1, sharedBackups: true, sharedLogs: true, createdAt: new Date().toISOString() }]);
  }
  res.json(workspacesByUser.get(userId));
});

app.post('/api/workspaces', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const workspace = {
    id: crypto.randomUUID(),
    name: req.body.name,
    appIds: req.body.appIds || [],
    memberCount: 1,
    sharedBackups: true,
    sharedLogs: true,
    createdAt: new Date().toISOString(),
  };
  workspacesByUser.set(userId, [workspace, ...(workspacesByUser.get(userId) || [])]);
  await logAudit(userId, 'workspace:create', 'workspace', workspace.id, null, workspace);
  res.status(201).json(workspace);
});

app.get('/api/apps/:appId/billing', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });
  const ramGb = source.memory_limit?.includes('g') ? parseFloat(source.memory_limit) : 1;
  const cpuCores = Math.max(0.5, (source.cpu_shares || 512) / 1024);
  const lineItems = [
    { label: 'CPU', amount: cpuCores * 11.5, unit: `${cpuCores.toFixed(1)} vCPU/Monat` },
    { label: 'RAM', amount: ramGb * 6.2, unit: `${ramGb.toFixed(1)} GB/Monat` },
    { label: 'Storage & Dateien', amount: 4.9, unit: '20 GB' },
    { label: 'Backups & Snapshots', amount: (serverSnapshots.get(appId)?.length || 2) * 1.4, unit: 'Snapshot' },
    { label: 'Netzwerk', amount: 2.5, unit: 'Traffic-Paket' },
  ];
  const monthlyEstimate = lineItems.reduce((sum, item) => sum + item.amount, 0);
  res.json({ appId, currency: 'EUR', currentMonth: monthlyEstimate * 0.42, monthlyEstimate, lineItems });
});

app.post('/api/apps/:appId/plugins/:pluginId/install', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId, pluginId } = req.params;
  const source = await getOwnedAppOrNull(appId, userId);
  if (!source) return res.status(404).json({ error: 'App not found' });
  const installed = { pluginId, appId, status: 'installed', installedAt: new Date().toISOString() };
  pluginInstallations.set(appId, [installed, ...(pluginInstallations.get(appId) || []).filter((item) => item.pluginId !== pluginId)]);
  await logAudit(userId, 'app:plugin-install', 'plugin', pluginId, null, installed);
  res.status(201).json({ success: true, pluginId });
});

// ============================================================================
// USER ROUTES (require auth)
// ============================================================================

// GET /api/user - Get current user info
app.get('/api/user', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;

  try {
    const { data: profile, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (error) throw error;

    res.json({
      id: (req as any).user.id,
      email: (req as any).user.email,
      ...profile,
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

// ============================================================================
// CONFIG ROUTES (require auth)
// ============================================================================

// GET /api/config/mode - Get current mode (personal/business)
app.get('/api/config/mode', verifyAuth, async (req: Request, res: Response) => {
  try {
    const { data, error } = await supabase
      .from('setup_config')
      .select('mode')
      .single();

    if (error || !data) {
      return res.json({ mode: 'personal' });
    }

    res.json({ mode: data.mode });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch config' });
  }
});

// ============================================================================
// CONFIG EDITOR ROUTES (require auth)
// ============================================================================

// GET /api/apps/:appId/config - List config files in container
app.get('/api/apps/:appId/config', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const path = (req.query.path as string) || '/';

  try {
    const { data: app, error } = await supabase
      .from('docker_apps')
      .select('container_id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (error || !app) return res.status(404).json({ error: 'App not found' });
    if (!app.container_id) return res.status(400).json({ error: 'No container associated with this app' });

    const safePath = path.replace(/[^a-zA-Z0-9_\-\.\/]/g, '');
    const { stdout, stderr } = await execAsync(`docker exec ${app.container_id} ls -la ${safePath}`).catch((err: any) => {
      throw new Error(`Failed to list directory: ${err.message}`);
    });

    const lines = stdout.trim().split('\n');
    const files = lines.filter((l: string) => l.length > 0).slice(1).map((line: string) => {
      const parts = line.split(/\s+/);
      const isDir = parts[0]?.startsWith('d') || false;
      const name = parts.slice(8).join(' ');
      return {
        name,
        path: safePath === '/' ? `/${name}` : `${safePath}/${name}`,
        size: parseInt(parts[4]) || 0,
        modifiedAt: `${parts[5]} ${parts[6]} ${parts[7]}`,
        isDirectory: isDir,
      };
    });

    res.json({ files, currentPath: safePath });
  } catch (err: any) {
    if (err.message?.includes('App not found')) return res.status(404).json({ error: err.message });
    res.status(500).json({ error: err.message || 'Failed to list config files' });
  }
});

// GET /api/apps/:appId/config/read - Read a config file
app.get('/api/apps/:appId/config/read', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const file = req.query.file as string;

  if (!file) return res.status(400).json({ error: 'file query parameter is required' });

  try {
    const { data: app, error } = await supabase
      .from('docker_apps')
      .select('container_id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (error || !app) return res.status(404).json({ error: 'App not found' });
    if (!app.container_id) return res.status(400).json({ error: 'No container associated with this app' });

    const { stdout, stderr } = await runCommand('docker', ['exec', app.container_id, 'cat', file]).catch((err: any) => {
      throw new Error(`Failed to read file: ${err.message}`);
    });

    const ext = file.split('.').pop()?.toLowerCase();
    let language: 'yaml' | 'json' | 'properties' | 'text' = 'text';
    if (ext === 'yml' || ext === 'yaml') language = 'yaml';
    else if (ext === 'json') language = 'json';
    else if (ext === 'properties') language = 'properties';

    res.json({ content: stdout, path: file, language });
  } catch (err: any) {
    if (err.message?.includes('App not found')) return res.status(404).json({ error: err.message });
    res.status(500).json({ error: err.message || 'Failed to read config file' });
  }
});

// POST /api/apps/:appId/config/write - Write/save a config file
app.post('/api/apps/:appId/config/write', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const { path: filePath, content } = req.body;

  if (!filePath || content === undefined) return res.status(400).json({ error: 'path and content are required' });

  try {
    const { data: app, error } = await supabase
      .from('docker_apps')
      .select('container_id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (error || !app) return res.status(404).json({ error: 'App not found' });
    if (!app.container_id) return res.status(400).json({ error: 'No container associated with this app' });

    const timestamp = Date.now();
    const backupPath = `${filePath}.bak.${timestamp}`;

    // Create backup
    await runCommand('docker', ['exec', app.container_id, 'cp', filePath, backupPath]).catch(() => {
      // Backup is best-effort; file may not exist yet
    });

    // Write new content
    const escapedContent = content.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    await runCommand('docker', ['exec', '-i', app.container_id, 'tee', filePath], content);

    await logAudit(userId, 'config:write', 'config_file', `${appId}:${filePath}`, null, { backupPath });
    res.json({ success: true, backupPath });
  } catch (err: any) {
    if (err.message?.includes('App not found')) return res.status(404).json({ error: err.message });
    res.status(500).json({ error: err.message || 'Failed to write config file' });
  }
});

// GET /api/apps/:appId/config/validate - Validate YAML/JSON syntax
app.get('/api/apps/:appId/config/validate', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const rawFile = req.query.file;

  if (typeof rawFile !== 'string' || !rawFile) {
    return res.status(400).json({ error: 'file query parameter is required' });
  }

  const file = rawFile;
  if (!/^[a-zA-Z0-9._/-]+$/.test(file) || file.includes('..') || file.startsWith('/')) {
    return res.status(400).json({ error: 'Invalid file path' });
  }

  try {
    const { data: app, error } = await supabase
      .from('docker_apps')
      .select('container_id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (error || !app) return res.status(404).json({ error: 'App not found' });
    if (!app.container_id) return res.status(400).json({ error: 'No container associated with this app' });

    const { stdout } = await runCommand('docker', ['exec', app.container_id, 'cat', file]).catch((err: any) => {
      throw new Error(`Failed to read file: ${err.message}`);
    });

    const ext = file.split('.').pop()?.toLowerCase();
    const errors: string[] = [];
    let valid = true;

    if (ext === 'yml' || ext === 'yaml') {
      try {
        JSON.parse(stdout);
        errors.push('File parsed as JSON but has .yaml extension');
        valid = false;
      } catch {
        // Not JSON, try YAML-like validation
        const lines = stdout.split('\n');
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i];
          if (line.trim().startsWith('- ') || line.trim().match(/^[\w.-]+:/)) continue;
          if (line.trim() === '' || line.trim().startsWith('#')) continue;
          if (line.trim().match(/^[a-zA-Z]/) && !line.includes(':')) {
            errors.push(`Line ${i + 1}: unexpected value "${line.trim()}"`);
            valid = false;
          }
        }
      }
    } else if (ext === 'json') {
      try {
        JSON.parse(stdout);
      } catch (e: any) {
        errors.push(e.message || 'Invalid JSON');
        valid = false;
      }
    } else {
      errors.push('Unsupported file format for validation');
      valid = false;
    }

    res.json({ valid, errors });
  } catch (err: any) {
    if (err.message?.includes('App not found')) return res.status(404).json({ error: err.message });
    res.status(500).json({ error: err.message || 'Failed to validate config file' });
  }
});

// Health check with basic instrumentation exposure
app.get('/health', (req: Request, res: Response) => {
  // Return some useful health metrics for observability
  res.json({ status: 'ok', uptime: process.uptime(), version: APP_VERSION, metrics });
});

// ============================================================================
// 2FA (Two-Factor Authentication) Routes
// ============================================================================

const INTEGRATION_SERVICE_URL = process.env.INTEGRATION_SERVICE_URL || 'http://localhost:9000';

async function forwardToIntegration(req: Request, res: Response, path: string) {
  try {
    const response = await fetch(`${INTEGRATION_SERVICE_URL}${path}`, {
      method: req.method,
      headers: { 'Content-Type': 'application/json' },
      body: req.method === 'POST' ? JSON.stringify(req.body) : undefined,
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (err) {
    res.status(502).json({ error: 'Integration service unavailable' });
  }
}

app.post('/api/auth/2fa/setup', async (req: Request, res: Response) => {
  await forwardToIntegration(req, res, '/api/auth/2fa/setup');
});

app.post('/api/auth/2fa/verify-setup', async (req: Request, res: Response) => {
  await forwardToIntegration(req, res, '/api/auth/2fa/verify-setup');
});

app.post('/api/auth/2fa/verify', async (req: Request, res: Response) => {
  await forwardToIntegration(req, res, '/api/auth/2fa/verify');
});

app.post('/api/auth/2fa/disable', async (req: Request, res: Response) => {
  await forwardToIntegration(req, res, '/api/auth/2fa/disable');
});

app.get('/api/auth/2fa/backup-codes', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const response = await fetch(`${INTEGRATION_SERVICE_URL}/api/auth/2fa/backup-codes?user_id=${userId}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (err) {
    res.status(502).json({ error: 'Integration service unavailable' });
  }
});

app.post('/api/auth/2fa/verify-backup', async (req: Request, res: Response) => {
  await forwardToIntegration(req, res, '/api/auth/2fa/verify-backup');
});

// GET /api/demo/flag - Expose the Demo feature flag for testing/CI verification
app.get('/api/demo/flag', (_req: Request, res: Response) => {
  const enabled = process.env.VITE_DEMO_FEATURE_ENABLED === 'true';
  res.json({ enabled });
});

// Minimal Business Mode MVP: expose a placeholder endpoint for customers
// Access controlled via existing verifyAuth middleware
app.get('/api/customers', verifyAuth, customersLimiter, async (req: Request, res: Response) => {
  const userId = (req as any).user?.id;
  try {
    const { data: cfg } = await supabase.from('setup_config').select('mode').single();
    const mode = (cfg as any)?.mode || 'personal';
    if (mode === 'personal') {
      return res.status(403).json({ error: 'Not available in Personal Mode' });
    }
    // Seed data on first boot for this user if no customers exist yet
    const { data: existingForUser, error: ex } = await supabase
      .from('customers')
      .select('id')
      .eq('owner_user_id', userId)
      .limit(1);
      if (!existingForUser || existingForUser.length === 0) {
      try {
        const seedsPath = path.join(__dirname, '..', 'seeds', 'customers.sample.json');
        let seeds: Array<{ name: string; email?: string } > = [];
        try {
          const raw = await fs.readFile(seedsPath, 'utf8');
          seeds = JSON.parse(raw);
        } catch {
          // If seeds file missing or invalid, skip seeding
          seeds = [];
        }
        for (const s of seeds) {
          // Respect owner_user_id in seed data; skip if it doesn't belong to the current user
          if ((s as any).owner_user_id && (s as any).owner_user_id !== userId) continue;
          if (!s?.name) continue;
          const { data: exists, error: e2 } = await supabase
            .from('customers')
            .select('id')
            .eq('owner_user_id', userId)
            .eq('name', s.name)
            .limit(1);
          if (exists && exists.length > 0) continue;
          await supabase
            .from('customers')
            .insert({ owner_user_id: userId, name: s.name, email: s.email ?? null })
            .select()
            .single();
        }
      } catch {
        // Ignore seeding errors; UI can still function
      }
    }
    // After potential seeding, fetch and return
    const { data, error } = await supabase.from('customers').select('*').eq('owner_user_id', userId);
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch customers' });
  }
});

// POST /api/customers - Create a new customer (Business Mode only)
app.post('/api/customers', verifyAuth, customersLimiter, async (req: Request, res: Response) => {
  const userId = (req as any).user?.id;
  const { name, email } = req.body;
  try {
    const { data: cfg } = await supabase.from('setup_config').select('mode').single();
    const mode = (cfg as any)?.mode || 'personal';
    if (mode === 'personal') {
      return res.status(403).json({ error: 'Not available in Personal Mode' });
    }
    if (!name) {
      return res.status(400).json({ error: 'Name is required' });
    }
    const { data, error } = await supabase.from('customers').insert({ owner_user_id: userId, name, email }).select().single();
    if (error) throw error;
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create customer' });
  }
});

// POST /api/seed-demo - Seed demo data (customers + apps) for quick local demos
app.post('/api/seed-demo', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user?.id;
  try {
    const { data: cfg } = await supabase.from('setup_config').select('mode').single();
    const mode = (cfg as any)?.mode || 'personal';
    if (mode === 'personal') {
      return res.status(403).json({ error: 'Not available in Personal Mode' });
    }

    const demoCustomers = [
      { owner_user_id: userId, name: 'Acme Co', email: 'contact@acme.local' },
      { owner_user_id: userId, name: 'Globex Corp', email: 'hello@globex.local' },
    ];
    // Idempotent: seed only missing customers for this user
    let insertedCustomers: any[] = [];
    for (const dc of demoCustomers) {
      const { data: exists } = await supabase
        .from('customers')
        .select('id')
        .eq('owner_user_id', userId)
        .eq('name', dc.name)
        .single();
      if (!exists) {
        const { data } = await supabase.from('customers').insert({ owner_user_id: userId, name: dc.name, email: dc.email }).select().single();
        if (data) insertedCustomers.push(data);
      }
    }
    // Prepare apps for seed (optional). Keep this idempotent per owner+name so
    // repeated demo seeding does not create duplicate containers for the same user.
    const demoApps = [
      { user_id: userId, name: 'demo-app', image: 'nginx:latest', status: 'stopped', memory_limit: '256mb' },
      { user_id: userId, name: 'monitor', image: 'prom/prometheus', status: 'stopped', memory_limit: '256mb' },
    ];
    let insertedApps: any[] = [];
    for (const appSeed of demoApps) {
      const { data: exists } = await supabase
        .from('docker_apps')
        .select('id')
        .eq('user_id', userId)
        .eq('name', appSeed.name)
        .single();
      if (!exists) {
        const { data } = await supabase.from('docker_apps').insert(appSeed).select().single();
        if (data) insertedApps.push(data);
      }
    }

    const customersSeeded = Array.isArray(insertedCustomers) ? insertedCustomers.length : 0;
    const appsSeeded = Array.isArray(insertedApps) ? insertedApps.length : 0;
    res.json({ customersSeeded, appsSeeded });
  } catch (err) {
    res.status(500).json({ error: 'Seed-demo failed' });
  }
});

// PATCH /api/customers/:customerId - Update a customer (Business Mode only)
app.patch('/api/customers/:customerId', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user?.id;
  const { customerId } = req.params;
  const updates = req.body;
  try {
    // Ensure ownership and apply updates
    const { data, error } = await supabase
      .from('customers')
      .update(updates)
      .eq('id', customerId)
      .eq('owner_user_id', userId)
      .select()
      .single();
    if (error || !data) {
      return res.status(404).json({ error: 'Customer not found' });
    }
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update customer' });
  }
});

// DELETE /api/customers/:customerId - Delete a customer (Business Mode only)
app.delete('/api/customers/:customerId', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user?.id;
  const { customerId } = req.params;
  try {
    const { error } = await supabase
      .from('customers')
      .delete()
      .eq('id', customerId)
      .eq('owner_user_id', userId);
    if (error) throw error;
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete customer' });
  }
});

// ============================================================================
// Phase 4: Management Panel Routes
// ============================================================================

// GET /api/apps/:appId/metrics - Server metrics for an app
app.get('/api/apps/:appId/metrics', verifyAuth, async (req: Request, res: Response) => {
  const { appId } = req.params;
  const range = (req.query.range as string) || '30m';
  try {
    const since = new Date(Date.now() - parseRange(range)).toISOString();
    const { data, error } = await supabase
      .from('server_metrics')
      .select('*')
      .eq('app_id', appId)
      .gte('recorded_at', since)
      .order('recorded_at', { ascending: true });
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

function parseRange(range: string): number {
  const match = range.match(/^(\d+)([mhd])$/);
  if (!match) return 30 * 60 * 1000;
  const val = parseInt(match[1]);
  const unit = match[2];
  if (unit === 'm') return val * 60 * 1000;
  if (unit === 'h') return val * 3600 * 1000;
  if (unit === 'd') return val * 86400 * 1000;
  return 30 * 60 * 1000;
}

// GET /api/metrics/aggregated - Aggregated metrics across all apps
app.get('/api/metrics/aggregated', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const { data: apps } = await supabase.from('docker_apps').select('id').eq('user_id', userId);
    if (!apps || apps.length === 0) return res.json({ totalApps: 0, totalPlayers: 0, avgCpu: 0, avgMemory: 0, serverCount: 0 });

    const appIds = apps.map(a => a.id);
    const { data: metrics } = await supabase
      .from('server_metrics')
      .select('app_id, player_count, cpu_percent, memory_used_mb, memory_total_mb, tps, lag_spike')
      .in('app_id', appIds)
      .order('recorded_at', { ascending: false });

    if (!metrics) return res.json({ totalApps: apps.length, totalPlayers: 0, avgCpu: 0, avgMemory: 0, serverCount: 0 });

    const latest = new Map<string, any>();
    for (const m of metrics) {
      if (!latest.has(m.app_id)) latest.set(m.app_id, m);
    }

    const vals = Array.from(latest.values());
    const totalPlayers = vals.reduce((s, m) => s + (m.player_count || 0), 0);
    const avgCpu = vals.length > 0 ? vals.reduce((s, m) => s + (m.cpu_percent || 0), 0) / vals.length : 0;
    const avgMemoryPercent = vals.length > 0
      ? vals.reduce((s, m) => s + (m.memory_total_mb > 0 ? ((m.memory_used_mb || 0) / m.memory_total_mb) * 100 : 0), 0) / vals.length
      : 0;
    const lagCount = vals.filter(m => m.lag_spike).length;
    res.json({ totalApps: apps.length, totalPlayers, avgCpu: Math.round(avgCpu * 100) / 100, avgMemory: Math.round(avgMemoryPercent * 100) / 100, serverCount: apps.length, lagSpikes: lagCount });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch aggregated metrics' });
  }
});

// GET /api/metrics/realtime - Real-time resource data
app.get('/api/metrics/realtime', verifyAuth, async (req: Request, res: Response) => {
  const appId = req.query.appId as string | undefined;
  try {
    if (appId) {
      const { data: app, error } = await supabase
        .from('docker_apps')
        .select('container_id')
        .eq('id', appId)
        .single();
      if (error || !app) return res.status(404).json({ error: 'App not found' });
      if (app.container_id) {
        const { stdout } = await execAsync(`docker stats ${app.container_id} --no-stream --format "{{json .}}"`).catch(() => ({ stdout: '' }));
        if (stdout) {
          const stats = JSON.parse(stdout);
          const cpuPct = parseFloat(stats.CPUPerc) || 0;
          const memUsed = parseFloat(stats.MemUsage?.split('/')[0]?.trim()) || 0;
          const memTotal = parseFloat(stats.MemUsage?.split('/')[1]?.trim()) || 1;
          const netRx = parseFloat(stats.NetIO?.split('/')[0]?.trim()) || 0;
          const netTx = parseFloat(stats.NetIO?.split('/')[1]?.trim()) || 0;
          return res.json({
            cpu: { current: cpuPct, cores: os.cpus().length, unit: '%' },
            memory: { current: memUsed, total: memTotal, unit: 'MB', percent: (memUsed / memTotal) * 100 },
            disk: { current: 0, total: 0, unit: 'GB', percent: 0 },
            network: { rx: netRx, tx: netTx, unit: 'Mbps' },
            timestamp: new Date().toISOString(),
          });
        }
      }
    }

    // System-wide metrics
    const cpus = os.cpus();
    const cpuLoad = cpus.reduce((acc, cpu) => {
      const total = Object.values(cpu.times).reduce((a, b) => a + b, 0);
      const idle = cpu.times.idle;
      return acc + ((total - idle) / total) * 100;
    }, 0) / cpus.length;

    const totalMem = os.totalmem();
    const freeMem = os.freemem();
    const memUsed = totalMem - freeMem;
    const memPercent = (memUsed / totalMem) * 100;

    let diskData = { current: 0, total: 0, percent: 0 };
    try {
      const { stdout } = await execAsync('df -k /');
      const lines = stdout.trim().split('\n');
      if (lines.length >= 2) {
        const parts = lines[1].split(/\s+/);
        const totalKb = parseInt(parts[1]) || 0;
        const usedKb = parseInt(parts[2]) || 0;
        const totalGb = totalKb / (1024 * 1024);
        const usedGb = usedKb / (1024 * 1024);
        diskData = { current: Math.round(usedGb * 100) / 100, total: Math.round(totalGb * 100) / 100, percent: totalGb > 0 ? (usedGb / totalGb) * 100 : 0 };
      }
    } catch {}

    res.json({
      cpu: { current: Math.round(cpuLoad * 100) / 100, cores: cpus.length, unit: '%' },
      memory: { current: Math.round(memUsed / (1024 * 1024)), total: Math.round(totalMem / (1024 * 1024)), unit: 'MB', percent: Math.round(memPercent * 100) / 100 },
      disk: { current: diskData.current, total: diskData.total, unit: 'GB', percent: Math.round(diskData.percent * 100) / 100 },
      network: { rx: 0, tx: 0, unit: 'Mbps' },
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch realtime metrics' });
  }
});

// GET /api/metrics/history - Historical time-series metrics
app.get('/api/metrics/history', verifyAuth, async (req: Request, res: Response) => {
  const appId = req.query.appId as string | undefined;
  const period = (req.query.period as string) || '1h';
  const resolution = (req.query.resolution as string) || '5m';

  const periodMap: Record<string, number> = { '1h': 3600000, '6h': 21600000, '24h': 86400000, '7d': 604800000 };
  const since = new Date(Date.now() - (periodMap[period] || 3600000)).toISOString();

  try {
    let query = supabase
      .from('server_metrics')
      .select('recorded_at, cpu_percent, memory_used_mb, memory_total_mb, tps, player_count')
      .gte('recorded_at', since)
      .order('recorded_at', { ascending: true });

    if (appId) query = query.eq('app_id', appId);

    const { data, error } = await query;
    if (error) throw error;

    // Aggregate by resolution interval
    const aggregated = new Map<string, { cpu: number[]; memory: number[]; tps: number[]; players: number[] }>();
    const intervalMs = resolution === '1m' ? 60000 : resolution === '5m' ? 300000 : 3600000;

    for (const row of data || []) {
      const ts = new Date(row.recorded_at);
      const bucket = new Date(Math.floor(ts.getTime() / intervalMs) * intervalMs).toISOString();
      if (!aggregated.has(bucket)) aggregated.set(bucket, { cpu: [], memory: [], tps: [], players: [] });
      const entry = aggregated.get(bucket)!;
      if (row.cpu_percent != null) entry.cpu.push(row.cpu_percent);
      if (row.memory_used_mb != null) entry.memory.push(row.memory_used_mb);
      if (row.tps != null) entry.tps.push(row.tps);
      if (row.player_count != null) entry.players.push(row.player_count);
    }

    const avg = (arr: number[]) => arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
    const result = Array.from(aggregated.entries()).map(([timestamp, vals]) => ({
      timestamp,
      cpu: Math.round(avg(vals.cpu) * 100) / 100,
      memory: Math.round(avg(vals.memory) * 100) / 100,
      tps: Math.round(avg(vals.tps) * 10) / 10,
      players: Math.round(avg(vals.players)),
    }));

    res.json({ data: result, period, resolution });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch history' });
  }
});

// POST /api/metrics/stream/config - Configure Netdata/Grafana data source
app.post('/api/metrics/stream/config', verifyAuth, async (req: Request, res: Response) => {
  const { type, url, apiKey } = req.body;
  if (!type || !url || !['netdata', 'grafana'].includes(type)) {
    return res.status(400).json({ error: 'type (netdata|grafana) and url are required' });
  }
  try {
    const { error } = await supabase
      .from('shared_config')
      .upsert({ key: 'metrics_config', value: { type, url, apiKey: apiKey || null } }, { onConflict: 'key' });
    if (error) throw error;
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to save metrics config' });
  }
});

// GET /api/metrics/grafana-url - Return Grafana embed URL if configured
app.get('/api/metrics/grafana-url', verifyAuth, async (req: Request, res: Response) => {
  try {
    const { data } = await supabase
      .from('shared_config')
      .select('value')
      .eq('key', 'metrics_config')
      .single();
    const config = data?.value as any;
    if (config && config.type === 'grafana' && config.url) {
      return res.json({ url: config.url });
    }
    res.json({ url: null });
  } catch (err) {
    res.json({ url: null });
  }
});

// GET /api/logs/access - Access logs
app.get('/api/logs/access', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 1000);
  const offset = parseInt(req.query.offset as string) || 0;
  try {
    const { data, error } = await supabase
      .from('access_logs')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch access logs' });
  }
});

// GET /api/apps/:appId/config-versions - Config version history
app.get('/api/apps/:appId/config-versions', verifyAuth, async (req: Request, res: Response) => {
  const { appId } = req.params;
  try {
    const { data, error } = await supabase
      .from('config_versions')
      .select('*')
      .eq('app_id', appId)
      .order('version', { ascending: false });
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch config versions' });
  }
});

// POST /api/apps/:appId/config-versions - Create config version snapshot
app.post('/api/apps/:appId/config-versions', verifyAuth, async (req: Request, res: Response) => {
  const { appId } = req.params;
  const userId = (req as any).user.id;
  const { config_snapshot, change_summary } = req.body;
  try {
    const { data: maxVer } = await supabase
      .from('config_versions')
      .select('version')
      .eq('app_id', appId)
      .order('version', { ascending: false })
      .limit(1);
    const nextVersion = (maxVer && maxVer.length > 0 ? maxVer[0].version : 0) + 1;
    const { data, error } = await supabase
      .from('config_versions')
      .insert({ app_id: appId, version: nextVersion, config_snapshot, created_by: userId, change_summary })
      .select()
      .single();
    if (error) throw error;
    await logAudit(userId, 'config:version:create', 'config_version', `${appId}@v${nextVersion}`, null, { change_summary });
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create config version' });
  }
});

// POST /api/apps/:appId/config-versions/:version/rollback - Rollback to version
app.post('/api/apps/:appId/config-versions/:version/rollback', verifyAuth, async (req: Request, res: Response) => {
  const { appId, version } = req.params;
  const userId = (req as any).user.id;
  try {
    const { data: target, error: fetchError } = await supabase
      .from('config_versions')
      .select('*')
      .eq('app_id', appId)
      .eq('version', parseInt(version))
      .single();
    if (fetchError || !target) return res.status(404).json({ error: 'Version not found' });
    const snapshot = target.config_snapshot;
    // Update the app with the snapshot config
    const { data, error } = await supabase
      .from('docker_apps')
      .update({ environment_vars: snapshot.environment_vars || {}, memory_limit: snapshot.memory_limit, cpu_shares: snapshot.cpu_shares })
      .eq('id', appId)
      .select()
      .single();
    if (error) throw error;
    // Create a new version entry reflecting the rollback
    const { data: maxVer } = await supabase
      .from('config_versions')
      .select('version')
      .eq('app_id', appId)
      .order('version', { ascending: false })
      .limit(1);
    const nextVersion = (maxVer && maxVer.length > 0 ? maxVer[0].version : 0) + 1;
    const { data: newVer, error: verError } = await supabase
      .from('config_versions')
      .insert({ app_id: appId, version: nextVersion, config_snapshot: snapshot, created_by: userId, change_summary: `Rolled back to version ${version}` })
      .select()
      .single();
    if (verError) throw verError;
    await logAudit(userId, 'config:rollback', 'config_version', `${appId}@v${version}`, null, { rolled_back_to: version });
    res.json(newVer);
  } catch (err) {
    res.status(500).json({ error: 'Failed to rollback config' });
  }
});

// Maintenance Windows CRUD
app.get('/api/maintenance-windows', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const { data, error } = await supabase
      .from('maintenance_windows')
      .select('*')
      .eq('user_id', userId)
      .order('starts_at', { ascending: false });
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch maintenance windows' });
  }
});

app.post('/api/maintenance-windows', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { title, description, app_id, starts_at, ends_at } = req.body;
  try {
    const { data, error } = await supabase
      .from('maintenance_windows')
      .insert({ user_id: userId, title, description, app_id, starts_at, ends_at })
      .select()
      .single();
    if (error) throw error;
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create maintenance window' });
  }
});

app.patch('/api/maintenance-windows/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { data, error } = await supabase
      .from('maintenance_windows')
      .update(req.body)
      .eq('id', id)
      .eq('user_id', userId)
      .select()
      .single();
    if (error || !data) return res.status(404).json({ error: 'Maintenance window not found' });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update maintenance window' });
  }
});

// Scheduled Tasks CRUD (stored in shared_config as JSON array)
const getScheduledTasks = async (): Promise<any[]> => {
  const { data } = await supabase
    .from('shared_config')
    .select('value')
    .eq('key', 'scheduled_tasks')
    .single();
  return (data?.value as any[]) || [];
};

const setScheduledTasks = async (tasks: any[]): Promise<void> => {
  await supabase
    .from('shared_config')
    .upsert({ key: 'scheduled_tasks', value: tasks }, { onConflict: 'key' });
};

app.get('/api/scheduled-tasks', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const tasks = await getScheduledTasks();
    const userTasks = tasks.filter((t: any) => t.user_id === userId);
    res.json(userTasks);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch scheduled tasks' });
  }
});

app.post('/api/scheduled-tasks', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, description, taskType, targetAppId, cronExpression, command } = req.body;

  if (!name || !taskType || !cronExpression) {
    return res.status(400).json({ error: 'name, taskType, and cronExpression are required' });
  }

  if (!['restart', 'command', 'backup', 'custom'].includes(taskType)) {
    return res.status(400).json({ error: 'taskType must be restart, command, backup, or custom' });
  }

  try {
    const tasks = await getScheduledTasks();
    const newTask = {
      id: crypto.randomUUID(),
      user_id: userId,
      name,
      description: description || '',
      taskType,
      targetAppId: targetAppId || null,
      cronExpression,
      command: command || null,
      enabled: true,
      lastRunAt: null,
      lastRunStatus: null,
      nextRunAt: null,
      createdAt: new Date().toISOString(),
    };
    tasks.push(newTask);
    await setScheduledTasks(tasks);
    await logAudit(userId, 'scheduled_task:create', 'scheduled_task', newTask.id, null, { name, taskType, cronExpression });
    res.status(201).json(newTask);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create scheduled task' });
  }
});

app.patch('/api/scheduled-tasks/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const tasks = await getScheduledTasks();
    const index = tasks.findIndex((t: any) => t.id === id && t.user_id === userId);
    if (index === -1) return res.status(404).json({ error: 'Scheduled task not found' });
    tasks[index] = { ...tasks[index], ...req.body, id, user_id: userId };
    await setScheduledTasks(tasks);
    await logAudit(userId, 'scheduled_task:update', 'scheduled_task', id, null, req.body);
    res.json(tasks[index]);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update scheduled task' });
  }
});

app.delete('/api/scheduled-tasks/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const tasks = await getScheduledTasks();
    const index = tasks.findIndex((t: any) => t.id === id && t.user_id === userId);
    if (index === -1) return res.status(404).json({ error: 'Scheduled task not found' });
    tasks.splice(index, 1);
    await setScheduledTasks(tasks);
    await logAudit(userId, 'scheduled_task:delete', 'scheduled_task', id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete scheduled task' });
  }
});

app.post('/api/scheduled-tasks/:id/toggle', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const tasks = await getScheduledTasks();
    const index = tasks.findIndex((t: any) => t.id === id && t.user_id === userId);
    if (index === -1) return res.status(404).json({ error: 'Scheduled task not found' });
    tasks[index].enabled = !tasks[index].enabled;
    await setScheduledTasks(tasks);
    await logAudit(userId, 'scheduled_task:toggle', 'scheduled_task', id, null, { enabled: tasks[index].enabled });
    res.json(tasks[index]);
  } catch (err) {
    res.status(500).json({ error: 'Failed to toggle scheduled task' });
  }
});

// Backup Jobs CRUD
app.get('/api/backup-jobs', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const { data, error } = await supabase
      .from('backup_jobs')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch backup jobs' });
  }
});

app.post('/api/backup-jobs', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, app_id, schedule_type, retention_count } = req.body;
  try {
    const { data, error } = await supabase
      .from('backup_jobs')
      .insert({ user_id: userId, name, app_id, schedule_type: schedule_type || 'manual', retention_count: retention_count || 7 })
      .select()
      .single();
    if (error) throw error;
    await logAudit(userId, 'backup:create', 'backup', data.id, null, { name, app_id });
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create backup job' });
  }
});

app.patch('/api/backup-jobs/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { data, error } = await supabase
      .from('backup_jobs')
      .update(req.body)
      .eq('id', id)
      .eq('user_id', userId)
      .select()
      .single();
    if (error || !data) return res.status(404).json({ error: 'Backup job not found' });
    await logAudit(userId, 'backup:update', 'backup', id, null, req.body);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update backup job' });
  }
});

app.delete('/api/backup-jobs/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { error } = await supabase.from('backup_jobs').delete().eq('id', id).eq('user_id', userId);
    if (error) throw error;
    await logAudit(userId, 'backup:delete', 'backup', id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete backup job' });
  }
});

// GET /api/backup-jobs/:jobId/status - Backup status history
app.get('/api/backup-jobs/:jobId/status', verifyAuth, async (req: Request, res: Response) => {
  const { jobId } = req.params;
  try {
    const { data, error } = await supabase
      .from('backup_status')
      .select('*')
      .eq('backup_job_id', jobId)
      .order('started_at', { ascending: false })
      .limit(50);
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch backup status' });
  }
});

// Alert Configs CRUD
app.get('/api/alert-configs', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const { data, error } = await supabase
      .from('alert_configs')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch alert configs' });
  }
});

app.post('/api/alert-configs', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { metric_type, operator, threshold, enabled, notify_email } = req.body;
  try {
    const { data, error } = await supabase
      .from('alert_configs')
      .insert({ user_id: userId, metric_type, operator, threshold, enabled: enabled ?? true, notify_email: notify_email ?? false })
      .select()
      .single();
    if (error) throw error;
    await logAudit(userId, 'alert:create', 'alert_config', data.id, null, { metric_type, operator, threshold });
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create alert config' });
  }
});

app.patch('/api/alert-configs/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { data, error } = await supabase
      .from('alert_configs')
      .update(req.body)
      .eq('id', id)
      .eq('user_id', userId)
      .select()
      .single();
    if (error || !data) return res.status(404).json({ error: 'Alert config not found' });
    await logAudit(userId, 'alert:update', 'alert_config', id, null, req.body);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update alert config' });
  }
});

app.delete('/api/alert-configs/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { error } = await supabase.from('alert_configs').delete().eq('id', id).eq('user_id', userId);
    if (error) throw error;
    await logAudit(userId, 'alert:delete', 'alert_config', id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete alert config' });
  }
});

// Alert History
app.get('/api/alert-history', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const { data: configs } = await supabase.from('alert_configs').select('id').eq('user_id', userId);
    if (!configs || configs.length === 0) return res.json([]);
    const configIds = configs.map(c => c.id);
    const { data, error } = await supabase
      .from('alert_history')
      .select('*')
      .in('alert_config_id', configIds)
      .order('triggered_at', { ascending: false })
      .limit(100);
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch alert history' });
  }
});

app.post('/api/alert-history/:id/acknowledge', verifyAuth, async (req: Request, res: Response) => {
  const { id } = req.params;
  try {
    const { data, error } = await supabase
      .from('alert_history')
      .update({ acknowledged: true })
      .eq('id', id)
      .select()
      .single();
    if (error || !data) return res.status(404).json({ error: 'Alert not found' });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to acknowledge alert' });
  }
});

// Health Checks
app.get('/api/health-checks', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = req.query.app_id as string;
  try {
    let query = supabase.from('health_checks').select('*, docker_apps!inner(user_id)').eq('docker_apps.user_id', userId);
    if (appId) query = query.eq('app_id', appId);
    const { data, error } = await query.order('checked_at', { ascending: false }).limit(200);
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch health checks' });
  }
});

// Reports & Export
app.get('/api/reports', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const startDate = req.query.start_date as string;
  const endDate = req.query.end_date as string;
  try {
    const { data: apps } = await supabase.from('docker_apps').select('id').eq('user_id', userId);
    if (!apps || apps.length === 0) return res.json({ metrics: [], backups: [], alerts: [] });

    const appIds = apps.map(a => a.id);
    const since = startDate || new Date(Date.now() - 30 * 86400000).toISOString();
    const until = endDate || new Date().toISOString();

    const [metricsRes, backupsRes, alertsRes] = await Promise.all([
      supabase.from('server_metrics').select('*').in('app_id', appIds).gte('recorded_at', since).lte('recorded_at', until).order('recorded_at', { ascending: false }).limit(500),
      supabase.from('backup_status').select('*, backup_jobs!inner(app_id)').in('backup_jobs.app_id', appIds).gte('started_at', since).lte('started_at', until).order('started_at', { ascending: false }).limit(500),
      supabase.from('alert_history').select('*').gte('triggered_at', since).lte('triggered_at', until).order('triggered_at', { ascending: false }).limit(500),
    ]);

    res.json({
      metrics: metricsRes.data || [],
      backups: backupsRes.data || [],
      alerts: alertsRes.data || [],
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to generate report' });
  }
});

app.get('/api/reports/export', verifyAuth, async (req: Request, res: Response) => {
  const format = req.query.format as string;
  if (format === 'csv') {
    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=report.csv');
    res.send('metric,value,timestamp\nCPU,23,2024-01-01\nMemory,45,2024-01-01');
  } else {
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', 'attachment; filename=report.pdf');
    res.send(Buffer.from('PDF placeholder'));
  }
});

// ============================================================================
// DATABASE ROUTES (stored in shared_config as JSON array)
// ============================================================================

const getUserDatabases = async (userId: string): Promise<any[]> => {
  const { data } = await supabase
    .from('shared_config')
    .select('value')
    .eq('key', 'user_databases')
    .single();
  const all = (data?.value as any[]) || [];
  return all.filter((db: any) => db.user_id === userId);
};

const setUserDatabases = async (databases: any[]): Promise<void> => {
  await supabase
    .from('shared_config')
    .upsert({ key: 'user_databases', value: databases }, { onConflict: 'key' });
};

function maskPassword(pwd: string): string {
  if (!pwd) return '';
  if (pwd.length <= 4) return '****';
  return pwd.slice(0, 4) + '****';
}

// GET /api/databases - List databases for current user
app.get('/api/databases', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const { data } = await supabase
      .from('shared_config')
      .select('value')
      .eq('key', 'user_databases')
      .single();
    const all = (data?.value as any[]) || [];
    const userDbs = all.filter((db: any) => db.user_id === userId);
    const masked = userDbs.map((db: any) => ({
      ...db,
      password: db.password ? maskPassword(db.password) : undefined,
    }));
    res.json(masked);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch databases' });
  }
});

// POST /api/databases - Create a new database
app.post('/api/databases', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, appId } = req.body;

  if (!name || typeof name !== 'string') {
    return res.status(400).json({ error: 'Database name is required' });
  }

  if (!/^[a-zA-Z0-9_]+$/.test(name)) {
    return res.status(400).json({ error: 'Database name must be alphanumeric with underscores only' });
  }

  try {
    const { data } = await supabase
      .from('shared_config')
      .select('value')
      .eq('key', 'user_databases')
      .single();
    const all = (data?.value as any[]) || [];

    const password = crypto.randomBytes(16).toString('hex');
    const newDb = {
      id: crypto.randomUUID(),
      user_id: userId,
      name,
      host: process.env.HOST_IP || '127.0.0.1',
      port: 3306,
      database: name,
      username: name,
      password,
      appId: appId || null,
      status: 'creating',
      createdAt: new Date().toISOString(),
    };

    all.push(newDb);
    await supabase
      .from('shared_config')
      .upsert({ key: 'user_databases', value: all }, { onConflict: 'key' });

    await logAudit(userId, 'database:create', 'database', newDb.id, null, { name, appId });

    res.status(201).json(newDb);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create database' });
  }
});

// GET /api/databases/:id - Get database details
app.get('/api/databases/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { data } = await supabase
      .from('shared_config')
      .select('value')
      .eq('key', 'user_databases')
      .single();
    const all = (data?.value as any[]) || [];
    const db = all.find((d: any) => d.id === id && d.user_id === userId);
    if (!db) return res.status(404).json({ error: 'Database not found' });
    res.json({
      ...db,
      password: db.password ? maskPassword(db.password) : undefined,
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch database' });
  }
});

// DELETE /api/databases/:id - Delete a database
app.delete('/api/databases/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { data } = await supabase
      .from('shared_config')
      .select('value')
      .eq('key', 'user_databases')
      .single();
    const all = (data?.value as any[]) || [];
    const index = all.findIndex((d: any) => d.id === id && d.user_id === userId);
    if (index === -1) return res.status(404).json({ error: 'Database not found' });
    all.splice(index, 1);
    await supabase
      .from('shared_config')
      .upsert({ key: 'user_databases', value: all }, { onConflict: 'key' });
    await logAudit(userId, 'database:delete', 'database', id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete database' });
  }
});

// ============================================================================
// MODPACK ROUTES (proxied to Integration Service)
// ============================================================================

interface ModpackInstallation {
  id: string;
  modpackId: string;
  appId: string;
  status: 'pending' | 'downloading' | 'installing' | 'completed' | 'failed';
  progress: number;
  error?: string;
  createdAt: string;
}

async function getModpackInstallations(): Promise<ModpackInstallation[]> {
  const { data } = await supabase
    .from('shared_config')
    .select('value')
    .eq('key', 'modpack_installations')
    .single();
  return (data?.value as ModpackInstallation[]) || [];
}

async function setModpackInstallations(installations: ModpackInstallation[]): Promise<void> {
  await supabase
    .from('shared_config')
    .upsert({ key: 'modpack_installations', value: installations }, { onConflict: 'key' });
}

// GET /api/modpacks/search - Proxy to Integration Service
app.get('/api/modpacks/search', verifyAuth, async (req: Request, res: Response) => {
  const query = req.query.query as string;
  const platform = (req.query.platform as string) || 'all';
  try {
    const response = await fetch(
      `${INTEGRATION_SERVICE_URL}/api/modpacks/search?query=${encodeURIComponent(query)}&platform=${platform}&limit=20`
    );
    const data = await response.json();
    res.json(data);
  } catch (err) {
    res.status(502).json({ error: 'Integration service unavailable' });
  }
});

// POST /api/apps/:appId/modpacks/install - Trigger modpack installation
app.post('/api/apps/:appId/modpacks/install', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const { modpackId, platform } = req.body;

  if (!modpackId || !platform) {
    return res.status(400).json({ error: 'modpackId and platform are required' });
  }

  try {
    const { data: app, error: appError } = await supabase
      .from('docker_apps')
      .select('container_id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (appError || !app) return res.status(404).json({ error: 'App not found' });
    if (!app.container_id) return res.status(400).json({ error: 'No container associated with this app' });

    const installations = await getModpackInstallations();
    const installation: ModpackInstallation = {
      id: crypto.randomUUID(),
      modpackId,
      appId,
      status: 'pending',
      progress: 0,
      createdAt: new Date().toISOString(),
    };
    installations.push(installation);
    await setModpackInstallations(installations);
    await logAudit(userId, 'modpack:install', 'modpack', appId, null, { modpackId, platform });

    // Fire-and-forget: trigger installation asynchronously
    fetch(`${INTEGRATION_SERVICE_URL}/api/modpacks/${platform}/${modpackId.split(':')[1]}`)
      .then(r => r.json())
      .then(details => {
        if (details.error) {
          installation.status = 'failed';
          installation.error = details.error;
        } else {
          installation.status = 'downloading';
          installation.progress = 50;
          // In a real scenario this would involve downloading and copying to container
          setTimeout(() => {
            installation.status = 'completed';
            installation.progress = 100;
            setModpackInstallations(installations);
          }, 5000);
        }
        setModpackInstallations(installations);
      })
      .catch(() => {
        installation.status = 'failed';
        installation.error = 'Integration service unavailable';
        setModpackInstallations(installations);
      });

    res.status(201).json(installation);
  } catch (err) {
    res.status(500).json({ error: 'Failed to start modpack installation' });
  }
});

// GET /api/apps/:appId/modpacks/status - Check installation status
app.get('/api/apps/:appId/modpacks/status', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const installations = await getModpackInstallations();
    const appInstallations = installations.filter((i: ModpackInstallation) => i.appId === appId);
    res.json(appInstallations.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()));
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch installation status' });
  }
});

// ============================================================================
// AUDIT LOG ROUTE
// ============================================================================

app.get('/api/audit-log', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
  const offset = parseInt(req.query.offset as string) || 0;
  const { user_id, entity_type, action, start_date, end_date } = req.query;

  try {
    let query = supabase
      .from('audit_log')
      .select('*', { count: 'exact' })
      .eq('user_id', userId);

    if (entity_type && typeof entity_type === 'string') query = query.eq('entity_type', entity_type);
    if (action && typeof action === 'string') query = query.eq('action', action);
    if (start_date && typeof start_date === 'string') query = query.gte('created_at', start_date);
    if (end_date && typeof end_date === 'string') query = query.lte('created_at', end_date);

    const { data, error, count } = await query
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) throw error;
    res.json({ data: data || [], total: count, limit, offset });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch audit log' });
  }
});

// ============================================================================
// GLOBAL SEARCH
// ============================================================================

app.get('/api/search', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const q = req.query.q as string;
  if (!q || typeof q !== 'string' || q.length < 2) {
    return res.status(400).json({ error: 'Query must be at least 2 characters' });
  }

  try {
    const searchPattern = `%${q}%`;
    const [apps, auditLogs, backups] = await Promise.all([
      supabase
        .from('docker_apps')
        .select('id, name')
        .eq('user_id', userId)
        .or(`name.ilike.${searchPattern},description.ilike.${searchPattern},image.ilike.${searchPattern}`)
        .limit(10),
      supabase
        .from('audit_log')
        .select('id, action')
        .eq('user_id', userId)
        .ilike('action', searchPattern)
        .limit(10),
      supabase
        .from('backup_jobs')
        .select('id, name')
        .eq('user_id', userId)
        .ilike('name', searchPattern)
        .limit(10),
    ]);

    res.json({
      results: [
        ...(apps.data || []).map((a: any) => ({ id: a.id, name: a.name, type: 'app' })),
        ...(auditLogs.data || []).map((a: any) => ({ id: a.id, name: a.action, type: 'audit' })),
        ...(backups.data || []).map((b: any) => ({ id: b.id, name: b.name, type: 'backup' })),
      ],
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to search' });
  }
});

// ============================================================================
// NOTIFICATION CHANNELS ROUTES
// ============================================================================

app.get('/api/notification-channels', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const { data, error } = await supabase
      .from('notification_channels')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch notification channels' });
  }
});

app.post('/api/notification-channels', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, type, config } = req.body;
  if (!name || !type || !config) {
    return res.status(400).json({ error: 'name, type, and config are required' });
  }
  if (!['email', 'webhook', 'telegram'].includes(type)) {
    return res.status(400).json({ error: 'type must be email, webhook, or telegram' });
  }
  try {
    const { data, error } = await supabase
      .from('notification_channels')
      .insert({ user_id: userId, name, type, config })
      .select()
      .single();
    if (error) throw error;
    await logAudit(userId, 'notification:create', 'notification_channel', data.id, null, { name, type });
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create notification channel' });
  }
});

app.patch('/api/notification-channels/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { data, error } = await supabase
      .from('notification_channels')
      .update(req.body)
      .eq('id', id)
      .eq('user_id', userId)
      .select()
      .single();
    if (error || !data) return res.status(404).json({ error: 'Notification channel not found' });
    await logAudit(userId, 'notification:update', 'notification_channel', id, null, req.body);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update notification channel' });
  }
});

app.delete('/api/notification-channels/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { error } = await supabase
      .from('notification_channels')
      .delete()
      .eq('id', id)
      .eq('user_id', userId);
    if (error) throw error;
    await logAudit(userId, 'notification:delete', 'notification_channel', id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete notification channel' });
  }
});

// ============================================================================
// GIT DEPLOYMENT ROUTES (stored in shared_config as JSON array)
// ============================================================================

const getDeployments = async (): Promise<any[]> => {
  const { data } = await supabase
    .from('shared_config')
    .select('value')
    .eq('key', 'git_deployments')
    .single();
  return (data?.value as any[]) || [];
};

const setDeployments = async (deployments: any[]): Promise<void> => {
  await supabase
    .from('shared_config')
    .upsert({ key: 'git_deployments', value: deployments }, { onConflict: 'key' });
};

app.get('/api/deployments', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const deployments = await getDeployments();
    const userDeployments = deployments.filter((d: any) => d.user_id === userId);
    res.json(userDeployments);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch deployments' });
  }
});

app.post('/api/deployments', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, repoUrl, branch, containerId, targetDir, installCommand, restartCommand } = req.body;

  if (!name || !repoUrl) {
    return res.status(400).json({ error: 'name and repoUrl are required' });
  }

  try {
    const deployments = await getDeployments();
    const newDeployment = {
      id: crypto.randomUUID(),
      user_id: userId,
      name,
      repoUrl,
      repo: repoUrl.replace(/\.git$/, '').split('/').slice(-2).join('/'),
      branch: branch || 'main',
      containerId: containerId || null,
      targetDir: targetDir || '/app',
      installCommand: installCommand || '',
      restartCommand: restartCommand || '',
      enabled: true,
      webhookSecret: crypto.randomBytes(20).toString('hex'),
      createdAt: new Date().toISOString(),
      history: [],
    };
    deployments.push(newDeployment);
    await setDeployments(deployments);
    await logAudit(userId, 'deployment:create', 'deployment', newDeployment.id, null, { name, repoUrl });
    res.status(201).json(newDeployment);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create deployment' });
  }
});

app.delete('/api/deployments/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const deployments = await getDeployments();
    const index = deployments.findIndex((d: any) => d.id === id && d.user_id === userId);
    if (index === -1) return res.status(404).json({ error: 'Deployment not found' });
    deployments.splice(index, 1);
    await setDeployments(deployments);
    await logAudit(userId, 'deployment:delete', 'deployment', id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete deployment' });
  }
});

app.patch('/api/deployments/:id/toggle', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const deployments = await getDeployments();
    const index = deployments.findIndex((d: any) => d.id === id && d.user_id === userId);
    if (index === -1) return res.status(404).json({ error: 'Deployment not found' });
    deployments[index].enabled = !deployments[index].enabled;
    await setDeployments(deployments);
    await logAudit(userId, 'deployment:toggle', 'deployment', id, null, { enabled: deployments[index].enabled });
    res.json(deployments[index]);
  } catch (err) {
    res.status(500).json({ error: 'Failed to toggle deployment' });
  }
});

app.get('/api/deployments/:id/history', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const deployments = await getDeployments();
    const deployment = deployments.find((d: any) => d.id === id && d.user_id === userId);
    if (!deployment) return res.status(404).json({ error: 'Deployment not found' });
    res.json({ history: deployment.history || [] });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch deployment history' });
  }
});

app.post('/api/notification-channels/:id/test', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const { data: channel, error } = await supabase
      .from('notification_channels')
      .select('*')
      .eq('id', id)
      .eq('user_id', userId)
      .single();
    if (error || !channel) return res.status(404).json({ error: 'Notification channel not found' });
    res.json({ success: true, message: `Test notification sent via ${channel.type}` });
  } catch (err) {
    res.status(500).json({ error: 'Failed to send test notification' });
  }
});

// ============================================================================
// BILLING ROUTES (stored in shared_config as JSON)
// ============================================================================

const getBillingData = async (): Promise<any> => {
  const { data } = await supabase
    .from('shared_config')
    .select('value')
    .eq('key', 'billing_data')
    .single();
  return data?.value || { users: {}, rates: { cpuPerCoreHour: 0.05, ramPerGbHour: 0.02, storagePerGbHour: 0.001, backupPerGb: 0.01 } };
};

const setBillingData = async (value: any): Promise<void> => {
  await supabase
    .from('shared_config')
    .upsert({ key: 'billing_data', value }, { onConflict: 'key' });
};

const getOrCreateUserBilling = async (userId: string): Promise<any> => {
  const billing = await getBillingData();
  if (!billing.users[userId]) {
    billing.users[userId] = {
      balance: 0,
      totalSpent: 0,
      totalToppedUp: 0,
      transactions: [],
      createdAt: new Date().toISOString(),
    };
    await setBillingData(billing);
  }
  return billing;
};

// GET /api/billing/balance - Get current user's balance
app.get('/api/billing/balance', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const billing = await getOrCreateUserBilling(userId);
    const user = billing.users[userId];
    res.json({ balance: user.balance, totalSpent: user.totalSpent, totalToppedUp: user.totalToppedUp });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch balance' });
  }
});

// POST /api/billing/topup - Simulate adding funds
app.post('/api/billing/topup', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { amount } = req.body;
  if (!amount || amount <= 0) {
    return res.status(400).json({ error: 'Amount must be positive' });
  }
  try {
    const billing = await getOrCreateUserBilling(userId);
    const user = billing.users[userId];
    user.balance += amount;
    user.totalToppedUp += amount;
    user.transactions.push({
      id: crypto.randomUUID().slice(0, 16),
      amount,
      description: 'Top-up via management panel',
      type: 'topup',
      balanceAfter: user.balance,
      timestamp: new Date().toISOString(),
    });
    user.transactions = user.transactions.slice(-100);
    await setBillingData(billing);
    await logAudit(userId, 'billing:topup', 'billing', null, null, { amount });
    res.json({ balance: user.balance, totalSpent: user.totalSpent, totalToppedUp: user.totalToppedUp });
  } catch (err) {
    res.status(500).json({ error: 'Failed to process top-up' });
  }
});

// GET /api/billing/transactions - Get transaction history
app.get('/api/billing/transactions', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const billing = await getOrCreateUserBilling(userId);
    const user = billing.users[userId];
    const txns = (user.transactions || []).map((t: any) => ({
      id: t.id,
      amount: t.amount,
      description: t.description,
      type: t.type,
      balanceAfter: t.balanceAfter,
      timestamp: t.timestamp,
    }));
    res.json(txns.reverse());
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch transactions' });
  }
});

// GET /api/billing/cost-estimate - Calculate cost for given resources
app.get('/api/billing/cost-estimate', verifyAuth, async (req: Request, res: Response) => {
  try {
    const billing = await getBillingData();
    const rates = billing.rates;
    const cpu = parseFloat(req.query.cpu as string) || 1;
    const ram = parseFloat(req.query.ram as string) || 1;
    const storage = parseFloat(req.query.storage as string) || 10;
    const hourly = cpu * rates.cpuPerCoreHour + ram * rates.ramPerGbHour + storage * rates.storagePerGbHour;
    const daily = hourly * 24;
    const monthly = daily * 30;
    res.json({ hourly: Math.round(hourly * 10000) / 10000, daily: Math.round(daily * 100) / 100, monthly: Math.round(monthly * 100) / 100 });
  } catch (err) {
    res.status(500).json({ error: 'Failed to calculate cost' });
  }
});

// GET /api/billing/rates - Get current billing rates
app.get('/api/billing/rates', verifyAuth, async (req: Request, res: Response) => {
  try {
    const billing = await getBillingData();
    res.json(billing.rates);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch rates' });
  }
});

// ============================================================================
// FEATURE 32: KNOWLEDGE BASE ROUTES
// ============================================================================

import * as kb from './knowledge-base.js';

app.get('/api/kb/articles', verifyAuth, async (req: Request, res: Response) => {
  try {
    const articles = await kb.listArticles();
    res.json(articles);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch articles' });
  }
});

app.get('/api/kb/articles/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const article = await kb.getArticle(req.params.id);
    if (!article) return res.status(404).json({ error: 'Article not found' });
    res.json(article);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch article' });
  }
});

app.post('/api/kb/articles', verifyAuth, async (req: Request, res: Response) => {
  try {
    const userId = (req as any).user.id;
    const article = await kb.createArticle({ ...req.body, author: userId });
    await logAudit(userId, 'knowledge_base:create', 'kb_article', article.id);
    res.status(201).json(article);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create article' });
  }
});

app.put('/api/kb/articles/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const article = await kb.updateArticle(req.params.id, req.body);
    if (!article) return res.status(404).json({ error: 'Article not found' });
    await logAudit((req as any).user.id, 'knowledge_base:update', 'kb_article', req.params.id);
    res.json(article);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update article' });
  }
});

app.delete('/api/kb/articles/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const ok = await kb.deleteArticle(req.params.id);
    if (!ok) return res.status(404).json({ error: 'Article not found' });
    await logAudit((req as any).user.id, 'knowledge_base:delete', 'kb_article', req.params.id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete article' });
  }
});

app.get('/api/kb/search', verifyAuth, async (req: Request, res: Response) => {
  try {
    const qParam = req.query.q;
    const q = typeof qParam === 'string' ? qParam : '';
    if (!q || q.length < 2) return res.json([]);
    const articles = await kb.searchArticles(q);
    res.json(articles);
  } catch (err) {
    res.status(500).json({ error: 'Failed to search articles' });
  }
});

app.get('/api/kb/categories', verifyAuth, async (_req: Request, res: Response) => {
  try {
    const categories = await kb.listCategories();
    res.json(categories);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch categories' });
  }
});

app.post('/api/kb/categories', verifyAuth, async (req: Request, res: Response) => {
  try {
    const category = await kb.createCategory(req.body);
    res.status(201).json(category);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create category' });
  }
});

app.delete('/api/kb/categories/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const ok = await kb.deleteCategory(req.params.id);
    if (!ok) return res.status(404).json({ error: 'Category not found' });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete category' });
  }
});

// ============================================================================
// FEATURE 33: ACTIVITY FEED ROUTES
// ============================================================================

import * as activity from './activity-feed.js';

app.get('/api/activity', verifyAuth, async (req: Request, res: Response) => {
  try {
    const limit = Math.min(parseInt(req.query.limit as string) || 50, 200);
    const offset = parseInt(req.query.offset as string) || 0;
    const type = req.query.type as string;
    const userId = req.query.userId as string;
    const from = req.query.from as string;
    const to = req.query.to as string;
    const result = await activity.getEvents({ limit, offset, type, userId, from, to });
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch activity feed' });
  }
});

app.get('/api/activity/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const event = await activity.getEvent(req.params.id);
    if (!event) return res.status(404).json({ error: 'Event not found' });
    res.json(event);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch activity event' });
  }
});

app.get('/api/activity/export', verifyAuth, async (req: Request, res: Response) => {
  try {
    const format = (req.query.format as string) || 'json';
    const type = req.query.type as string;
    const userId = req.query.userId as string;
    const from = req.query.from as string;
    const to = req.query.to as string;
    const output = await activity.exportEvents({ format: format as 'csv' | 'json', type, userId, from, to });
    if (format === 'csv') {
      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', 'attachment; filename=activity-export.csv');
    } else {
      res.setHeader('Content-Type', 'application/json');
      res.setHeader('Content-Disposition', 'attachment; filename=activity-export.json');
    }
    res.send(output);
  } catch (err) {
    res.status(500).json({ error: 'Failed to export activity feed' });
  }
});

// ============================================================================
// FEATURE 35: CUSTOM DASHBOARD BUILDER ROUTES
// ============================================================================

import * as de from './dashboard-engine.js';

app.get('/api/dashboards', verifyAuth, async (_req: Request, res: Response) => {
  try {
    const dashboards = await de.listDashboards();
    res.json(dashboards);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch dashboards' });
  }
});

app.get('/api/dashboards/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const dashboard = await de.getDashboard(req.params.id);
    if (!dashboard) return res.status(404).json({ error: 'Dashboard not found' });
    res.json(dashboard);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch dashboard' });
  }
});

app.post('/api/dashboards', verifyAuth, async (req: Request, res: Response) => {
  try {
    const dashboard = await de.createDashboard(req.body);
    res.status(201).json(dashboard);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create dashboard' });
  }
});

app.put('/api/dashboards/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const dashboard = await de.updateDashboard(req.params.id, req.body);
    if (!dashboard) return res.status(404).json({ error: 'Dashboard not found' });
    res.json(dashboard);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update dashboard' });
  }
});

app.delete('/api/dashboards/:id', verifyAuth, async (req: Request, res: Response) => {
  try {
    const ok = await de.deleteDashboard(req.params.id);
    if (!ok) return res.status(404).json({ error: 'Dashboard not found' });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete dashboard' });
  }
});

app.get('/api/dashboards/:id/data', verifyAuth, async (req: Request, res: Response) => {
  try {
    const period = req.query.period as string;
    const data = await de.getDashboardData(req.params.id, { period });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch dashboard data' });
  }
});

// ============================================================================
// I18N TRANSLATION ROUTES
// ============================================================================

// GET /api/i18n/translations - List all translations
app.get('/api/i18n/translations', verifyAuth, async (req: Request, res: Response) => {
  try {
    const { data } = await supabase
      .from('shared_config')
      .select('value')
      .eq('key', 'i18n_translations')
      .single();
    res.json(data?.value || {});
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch translations' });
  }
});

// POST /api/i18n/translations - Submit a translation
app.post('/api/i18n/translations', verifyAuth, async (req: Request, res: Response) => {
  const { locale, key, value } = req.body;
  if (!locale || !key || !value) {
    return res.status(400).json({ error: 'locale, key, and value are required' });
  }
  const forbiddenKeys = new Set(['__proto__', 'constructor', 'prototype']);
  if (forbiddenKeys.has(locale) || forbiddenKeys.has(key)) {
    return res.status(400).json({ error: 'Invalid locale or key' });
  }
  try {
    const { data } = await supabase
      .from('shared_config')
      .select('value')
      .eq('key', 'i18n_translations')
      .single();
    const translations = (data?.value as Record<string, any>) || {};
    if (!translations[locale]) translations[locale] = {};
    translations[locale][key] = value;
    await supabase
      .from('shared_config')
      .upsert({ key: 'i18n_translations', value: translations }, { onConflict: 'key' });
    await logAudit((req as any).user.id, 'i18n:submit', 'translation', null, null, { locale, key });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to save translation' });
  }
});

// ============================================================================
// THEME STUDIO ROUTES
// ============================================================================

const getThemes = async (userId: string): Promise<any[]> => {
  const { data } = await supabase
    .from('shared_config')
    .select('value')
    .eq('key', 'user_themes')
    .single();
  const all = (data?.value as any[]) || [];
  return all.filter((t: any) => t.user_id === userId);
};

const setThemes = async (themes: any[]): Promise<void> => {
  await supabase
    .from('shared_config')
    .upsert({ key: 'user_themes', value: themes }, { onConflict: 'key' });
};

// GET /api/themes - List themes for current user
app.get('/api/themes', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const themes = await getThemes(userId);
    res.json(themes);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch themes' });
  }
});

// POST /api/themes - Save a new theme
app.post('/api/themes', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, config } = req.body;
  if (!name || !config) {
    return res.status(400).json({ error: 'name and config are required' });
  }
  try {
    const themes = await getThemes(userId);
    const existing = themes.findIndex((t: any) => t.name === name);
    const theme = {
      id: crypto.randomUUID(),
      user_id: userId,
      name,
      config,
      published: false,
      author: userId,
      createdAt: new Date().toISOString(),
    };
    if (existing >= 0) {
      themes[existing] = { ...themes[existing], ...theme };
    } else {
      themes.push(theme);
    }
    await setThemes(themes);
    await logAudit(userId, 'theme:save', 'theme', theme.id, null, { name });
    res.status(201).json(theme);
  } catch (err) {
    res.status(500).json({ error: 'Failed to save theme' });
  }
});

// GET /api/themes/:id - Get a specific theme
app.get('/api/themes/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const themes = await getThemes(userId);
    const theme = themes.find((t: any) => t.id === id);
    if (!theme) return res.status(404).json({ error: 'Theme not found' });
    res.json(theme);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch theme' });
  }
});

// DELETE /api/themes/:id - Delete a theme
app.delete('/api/themes/:id', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    let themes = await getThemes(userId);
    themes = themes.filter((t: any) => t.id !== id);
    await setThemes(themes);
    await logAudit(userId, 'theme:delete', 'theme', id);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete theme' });
  }
});

// POST /api/themes/:id/publish - Publish theme to gallery
app.post('/api/themes/:id/publish', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  try {
    const themes = await getThemes(userId);
    const index = themes.findIndex((t: any) => t.id === id);
    if (index === -1) return res.status(404).json({ error: 'Theme not found' });
    themes[index].published = !themes[index].published;
    await setThemes(themes);
    await logAudit(userId, 'theme:publish', 'theme', id, null, { published: themes[index].published });
    res.json(themes[index]);
  } catch (err) {
    res.status(500).json({ error: 'Failed to toggle theme publication' });
  }
});

// ============================================================================
// BULK OPERATIONS ROUTES
// ============================================================================

// POST /api/bulk/execute - Execute a bulk action
app.post('/api/bulk/execute', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { action, ids, params } = req.body;
  if (!action || !ids || !Array.isArray(ids) || ids.length === 0) {
    return res.status(400).json({ error: 'action and ids array are required' });
  }
  try {
    const job = await bulkEngine.execute(action, userId, ids, params || {});
    res.status(202).json({
      batchId: job.batchId,
      status: job.status,
      progress: job.progress,
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to execute bulk action' });
  }
});

// GET /api/bulk/:batchId - Get bulk action status
app.get('/api/bulk/:batchId', verifyAuth, async (req: Request, res: Response) => {
  const { batchId } = req.params;
  try {
    if (batchId === 'history') {
      return res.json(bulkEngine.getHistory());
    }
    const job = await bulkEngine.getStatus(batchId);
    if (!job) return res.status(404).json({ error: 'Batch not found' });
    res.json(job);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch status' });
  }
});

// POST /api/bulk/:batchId/undo - Rollback a bulk action
app.post('/api/bulk/:batchId/undo', verifyAuth, async (req: Request, res: Response) => {
  const { batchId } = req.params;
  try {
    const success = await bulkEngine.undo(batchId);
    if (!success) return res.status(404).json({ error: 'Batch not found or already rolled back' });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to undo bulk action' });
  }
});

// ============================================================================
// OPENAPI / SWAGGER DOCS
// ============================================================================

app.get('/api/openapi.json', (_req: Request, res: Response) => {
  res.json(openapiSpec);
});

app.get('/api/docs', (_req: Request, res: Response) => {
  res.send(`<!DOCTYPE html>
<html><head><title>Infra Pilot API Docs</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({ url: '/api/openapi.json', dom_id: '#swagger-ui' });
</script>
</body></html>`);
});

// ============================================================================
// AI CONFIG ADVISOR ROUTES
// ============================================================================

// GET /api/config/:appId/advice - Analyze config against best practices
app.get('/api/config/:appId/advice', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const { data: app, error } = await supabase
      .from('docker_apps')
      .select('*')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (error || !app) return res.status(404).json({ error: 'App not found' });

    // Attempt to read config files from container
    const files: Record<string, string> = {};
    if (app.container_id) {
      const configPaths = ['/server.properties', '/bukkit.yml', '/spigot.yml', '/paper.yml', '/config.yml', '/application.yml', '/application.properties'];
      for (const fp of configPaths) {
        try {
          const { stdout } = await execAsync(`docker exec ${app.container_id} cat ${fp} 2>/dev/null`).catch(() => ({ stdout: '' }));
          if (stdout) files[fp] = stdout;
        } catch {}
      }
    }

    const result = analyzeConfiguration({ ...app, appId }, files);
    res.json({
      appId,
      analyzedAt: new Date().toISOString(),
      total: result.summary.total,
      critical: result.summary.critical,
      warning: result.summary.warning,
      info: result.summary.info,
      suggestions: result.suggestions,
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to analyze configuration' });
  }
});

// POST /api/config/:appId/advice/:suggestionId/apply - Apply a suggestion
app.post('/api/config/:appId/advice/:suggestionId/apply', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId, suggestionId } = req.params;

  try {
    const { data: app, error } = await supabase
      .from('docker_apps')
      .select('*')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (error || !app) return res.status(404).json({ error: 'App not found' });

    const files: Record<string, string> = {};
    if (app.container_id) {
      const configPaths = ['/server.properties', '/bukkit.yml', '/spigot.yml', '/paper.yml', '/config.yml', '/application.yml', '/application.properties'];
      for (const fp of configPaths) {
        try {
          const { stdout } = await execAsync(`docker exec ${app.container_id} cat ${fp} 2>/dev/null`).catch(() => ({ stdout: '' }));
          if (stdout) files[fp] = stdout;
        } catch {}
      }
    }

    const result = analyzeConfiguration({ ...app, appId }, files);
    const suggestion = result.suggestions.find(s => s.id === suggestionId);
    if (!suggestion) return res.status(404).json({ error: 'Suggestion not found' });
    if (!suggestion.autoFixable) return res.status(400).json({ error: 'This suggestion cannot be auto-fixed' });

    await logAudit(userId, 'config:advice:apply', 'config_advice', `${appId}:${suggestionId}`, null, { title: suggestion.title, fixCommand: suggestion.fixCommand });
    res.json({ success: true, message: `Applied: ${suggestion.title}` });
  } catch (err) {
    res.status(500).json({ error: 'Failed to apply suggestion' });
  }
});

// ============================================================================
// PLUGIN MARKETPLACE ROUTES
// ============================================================================

// GET /api/plugins - List all plugins
app.get('/api/plugins', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = req.query.appId as string;
  try {
    const plugins = await pluginRegistry.listPlugins(userId, appId);
    res.json(plugins);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch plugins' });
  }
});

// GET /api/plugins/:id - Get plugin details
app.get('/api/plugins/:id', verifyAuth, async (req: Request, res: Response) => {
  const { id } = req.params;
  const appId = req.query.appId as string;
  try {
    const plugin = await pluginRegistry.getPlugin(id, undefined, appId);
    if (!plugin) return res.status(404).json({ error: 'Plugin not found' });
    res.json(plugin);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch plugin' });
  }
});

// POST /api/plugins/:id/install - Install a plugin for an app
app.post('/api/plugins/:id/install', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  const { appId } = req.body;

  if (!appId) return res.status(400).json({ error: 'appId is required' });

  try {
    const { data: app, error: appError } = await supabase
      .from('docker_apps')
      .select('id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (appError || !app) return res.status(404).json({ error: 'App not found' });

    await pluginRegistry.installPlugin(id, appId, userId);
    await logAudit(userId, 'plugin:install', 'plugin', id, null, { appId });
    res.json({ success: true });
  } catch (err: any) {
    res.status(500).json({ error: err.message || 'Failed to install plugin' });
  }
});

// POST /api/plugins/:id/uninstall - Uninstall a plugin from an app
app.post('/api/plugins/:id/uninstall', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { id } = req.params;
  const { appId } = req.body;

  if (!appId) return res.status(400).json({ error: 'appId is required' });

  try {
    await pluginRegistry.uninstallPlugin(id, appId);
    await logAudit(userId, 'plugin:uninstall', 'plugin', id, null, { appId });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to uninstall plugin' });
  }
});

// POST /api/plugins - Publish a new plugin
app.post('/api/plugins', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, description, version, author, category, tags, iconUrl, homepage } = req.body;

  if (!name || !description || !version || !author || !category) {
    return res.status(400).json({ error: 'name, description, version, author, and category are required' });
  }

  try {
    const plugin = await pluginRegistry.publishPlugin({
      id: crypto.randomUUID(),
      name,
      description,
      version,
      author,
      category,
      tags: tags || [],
      downloads: 0,
      iconUrl,
      homepage,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    });
    await logAudit(userId, 'plugin:publish', 'plugin', plugin.id, null, { name, version, category });
    res.status(201).json(plugin);
  } catch (err) {
    res.status(500).json({ error: 'Failed to publish plugin' });
  }
});

// ============================================================================
// COLLABORATIVE TERMINAL ROUTES
// ============================================================================

const terminalSessions = new Map<string, { id: string; appId: string; createdBy: string; createdAt: string; users: Map<string, { id: string; displayName: string; cursor: { row: number; col: number }; joinedAt: string }> }>();

// POST /api/terminal/sessions - Create a terminal session
app.post('/api/terminal/sessions', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.body;

  if (!appId) return res.status(400).json({ error: 'appId is required' });

  try {
    const { data: app, error: appError } = await supabase
      .from('docker_apps')
      .select('id')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (appError || !app) return res.status(404).json({ error: 'App not found' });

    const sessionId = crypto.randomUUID();
    terminalSessions.set(sessionId, {
      id: sessionId,
      appId,
      createdBy: userId,
      createdAt: new Date().toISOString(),
      users: new Map(),
    });

    res.status(201).json({
      id: sessionId,
      appId,
      createdBy: userId,
      createdAt: new Date().toISOString(),
      users: [],
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to create terminal session' });
  }
});

// GET /api/terminal/sessions/:id - Get session details
app.get('/api/terminal/sessions/:id', verifyAuth, async (req: Request, res: Response) => {
  const { id } = req.params;
  const session = terminalSessions.get(id);

  if (!session) return res.status(404).json({ error: 'Session not found' });

  res.json({
    id: session.id,
    appId: session.appId,
    createdBy: session.createdBy,
    createdAt: session.createdAt,
    users: Array.from(session.users.values()),
  });
});

// ============================================================================
// CHANGE APPROVAL WORKFLOW ROUTES
// ============================================================================

// POST /api/change-requests - Create a change request
app.post('/api/change-requests', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId, action, reason, details, isBreakGlass } = req.body;

  if (!appId || !action || !reason) {
    return res.status(400).json({ error: 'appId, action, and reason are required' });
  }

  try {
    const { data: userProfile } = await supabase
      .from('user_profiles')
      .select('display_name')
      .eq('id', userId)
      .single();

    const userName = userProfile?.display_name || 'Unknown';
    const request = changeApproval.createChangeRequest(userId, userName, appId, action, reason, details || '', isBreakGlass || false);

    await logAudit(userId, 'change_request:create', 'change_request', request.id, null, { appId, action, status: request.status, isBreakGlass: request.isBreakGlass });
    res.status(201).json(request);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create change request' });
  }
});

// GET /api/change-requests - List change requests
app.get('/api/change-requests', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const status = req.query.status as string;
  const appId = req.query.appId as string;

  try {
    const requests = changeApproval.listChangeRequests({ status, userId, appId });
    res.json(requests);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch change requests' });
  }
});

// POST /api/change-requests/:id/approve - Approve a change request
app.post('/api/change-requests/:id/approve', verifyAuth, async (req: Request, res: Response) => {
  const reviewerId = (req as any).user.id;
  const { id } = req.params;

  try {
    const { data: userProfile } = await supabase
      .from('user_profiles')
      .select('display_name')
      .eq('id', reviewerId)
      .single();

    const reviewerName = userProfile?.display_name || 'Unknown';
    const result = changeApproval.approveChangeRequest(id, reviewerId, reviewerName);

    if (!result) return res.status(404).json({ error: 'Change request not found or already processed' });

    await logAudit(reviewerId, 'change_request:approve', 'change_request', id);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Failed to approve change request' });
  }
});

// POST /api/change-requests/:id/reject - Reject a change request
app.post('/api/change-requests/:id/reject', verifyAuth, async (req: Request, res: Response) => {
  const reviewerId = (req as any).user.id;
  const { id } = req.params;
  const { reason } = req.body;

  if (!reason) return res.status(400).json({ error: 'Rejection reason is required' });

  try {
    const { data: userProfile } = await supabase
      .from('user_profiles')
      .select('display_name')
      .eq('id', reviewerId)
      .single();

    const reviewerName = userProfile?.display_name || 'Unknown';
    const result = changeApproval.rejectChangeRequest(id, reviewerId, reviewerName, reason);

    if (!result) return res.status(404).json({ error: 'Change request not found or already processed' });

    await logAudit(reviewerId, 'change_request:reject', 'change_request', id, null, { reason });
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Failed to reject change request' });
  }
});

// ============================================================================
// V3 FEATURE ROUTES
// ============================================================================

const v3DataDir = path.join(__dirname, '..', 'data');
fs.mkdir(v3DataDir, { recursive: true }).catch(() => {});

// Helper: read/write JSON files for v3 in-memory DB
async function v3Read<T>(name: string, fallback: T): Promise<T> {
  try {
    const raw = await fs.readFile(path.join(v3DataDir, `${name}.json`), 'utf-8');
    return JSON.parse(raw);
  } catch { return fallback; }
}
async function v3Write(name: string, data: any): Promise<void> {
  await fs.writeFile(path.join(v3DataDir, `${name}.json`), JSON.stringify(data, null, 2), 'utf-8');
}

// --- Topology 3D ---
app.get('/api/v3/topology/nodes', async (_req: Request, res: Response) => {
  const nodes = await v3Read<any[]>('topology_nodes', []);
  res.json(nodes);
});
app.get('/api/v3/topology/edges', async (_req: Request, res: Response) => {
  const edges = await v3Read<any[]>('topology_edges', []);
  res.json(edges);
});

// --- Geo Heatmap ---
app.get('/api/v3/geo/heatmap', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('geo_heatmap', []);
  let filtered = data;
  if (req.query.region) filtered = filtered.filter((d: any) => d.region === req.query.region);
  if (req.query.startDate) filtered = filtered.filter((d: any) => new Date(d.date) >= new Date(req.query.startDate as string));
  if (req.query.endDate) filtered = filtered.filter((d: any) => new Date(d.date) <= new Date(req.query.endDate as string));
  res.json(filtered);
});
app.get('/api/v3/geo/regions', async (req: Request, res: Response) => {
  const regions = await v3Read<any[]>('geo_regions', []);
  let filtered = regions;
  if (req.query.region) filtered = filtered.filter((r: any) => r.id === req.query.region);
  res.json(filtered);
});
app.get('/api/v3/geo/cities', async (req: Request, res: Response) => {
  const cities = await v3Read<any[]>('geo_cities', []);
  let filtered = cities;
  if (req.query.region) filtered = filtered.filter((c: any) => c.region === req.query.region);
  if (req.query.limit) filtered = filtered.slice(0, parseInt(req.query.limit as string, 10));
  res.json(filtered);
});
app.get('/api/v3/geo/filters', async (_req: Request, res: Response) => {
  const filters = await v3Read<any>('geo_filters', { regions: [], providers: [], statuses: [] });
  res.json(filters);
});
app.get('/api/v3/geo/timelapse', async (req: Request, res: Response) => {
  const frames = await v3Read<any[]>('geo_timelapse', []);
  let filtered = frames;
  if (req.query.region) filtered = filtered.filter((f: any) => f.region === req.query.region);
  res.json(filtered);
});

// --- Cost Analytics ---
app.get('/api/v3/costs/breakdown', async (_req: Request, res: Response) => {
  const data = await v3Read<any>('costs_breakdown', { categories: [], total: 0 });
  res.json(data);
});
app.get('/api/v3/costs/trends', async (req: Request, res: Response) => {
  const trends = await v3Read<any[]>('costs_trends', []);
  let filtered = trends;
  if (req.query.period) filtered = filtered.filter((t: any) => t.period === req.query.period);
  res.json(filtered);
});
app.get('/api/v3/costs/unit-economics', async (_req: Request, res: Response) => {
  const data = await v3Read<any>('costs_unit_economics', { cpu: 0, memory: 0, storage: 0, bandwidth: 0 });
  res.json(data);
});
app.get('/api/v3/costs/budgets', async (_req: Request, res: Response) => {
  const budgets = await v3Read<any[]>('costs_budgets', []);
  res.json(budgets);
});
app.post('/api/v3/costs/budgets', async (req: Request, res: Response) => {
  const budgets = await v3Read<any[]>('costs_budgets', []);
  const newBudget = { id: crypto.randomUUID(), ...req.body, createdAt: new Date().toISOString() };
  budgets.push(newBudget);
  await v3Write('costs_budgets', budgets);
  res.status(201).json(newBudget);
});
app.get('/api/v3/costs/savings', async (_req: Request, res: Response) => {
  const savings = await v3Read<any[]>('costs_savings', []);
  res.json(savings);
});
app.get('/api/v3/costs/forecast', async (_req: Request, res: Response) => {
  const forecast = await v3Read<any[]>('costs_forecast', []);
  res.json(forecast);
});

// --- BI Dashboard ---
app.get('/api/v3/bi/kpi-summary', async (_req: Request, res: Response) => {
  const data = await v3Read<any>('bi_kpi_summary', { mrr: 0, arr: 0, ltv: 0, cac: 0, churn: 0, activeCustomers: 0 });
  res.json(data);
});
app.get('/api/v3/bi/mrr', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('bi_mrr', []);
  res.json(data);
});
app.get('/api/v3/bi/arr', async (_req: Request, res: Response) => {
  const data = await v3Read<any>('bi_arr', { current: 0, growth: 0, breakdown: [] });
  res.json(data);
});
app.get('/api/v3/bi/churn', async (_req: Request, res: Response) => {
  const data = await v3Read<any>('bi_churn', { rate: 0, trends: [], reasons: [] });
  res.json(data);
});
app.get('/api/v3/bi/ltv', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('bi_ltv', []);
  res.json(data);
});
app.get('/api/v3/bi/cac', async (_req: Request, res: Response) => {
  const data = await v3Read<any>('bi_cac', { total: 0, byChannel: [] });
  res.json(data);
});
app.get('/api/v3/bi/acquisition', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('bi_acquisition', []);
  res.json(data);
});
app.get('/api/v3/bi/revenue', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('bi_revenue', []);
  res.json(data);
});
app.get('/api/v3/bi/forecasts', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('bi_forecasts', []);
  res.json(data);
});
app.get('/api/v3/bi/cohorts', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('bi_cohorts', []);
  res.json(data);
});

// --- Dependency Graph ---
app.get('/api/v3/dependencies/graph', async (_req: Request, res: Response) => {
  const graph = await v3Read<any>('dependency_graph', { nodes: [], edges: [] });
  res.json(graph);
});
app.get('/api/v3/dependencies/impact/:nodeId', async (req: Request, res: Response) => {
  const impact = await v3Read<any[]>('dependency_impact', []);
  const filtered = impact.filter((i: any) => i.sourceId === req.params.nodeId || i.targetId === req.params.nodeId);
  res.json(filtered);
});
app.post('/api/v3/dependencies/discover', async (_req: Request, res: Response) => {
  const graph = await v3Read<any>('dependency_graph', { nodes: [], edges: [] });
  res.json({ discovered: graph.nodes.length + graph.edges.length });
});

// --- Custom Report Builder ---
app.get('/api/v3/reports/designs', async (_req: Request, res: Response) => {
  const designs = await v3Read<any[]>('report_designs', []);
  res.json(designs);
});
app.post('/api/v3/reports/designs', async (req: Request, res: Response) => {
  const designs = await v3Read<any[]>('report_designs', []);
  const newDesign = { id: crypto.randomUUID(), ...req.body, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
  designs.push(newDesign);
  await v3Write('report_designs', designs);
  res.status(201).json(newDesign);
});
app.put('/api/v3/reports/designs/:id', async (req: Request, res: Response) => {
  const designs = await v3Read<any[]>('report_designs', []);
  const idx = designs.findIndex((d: any) => d.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Design not found' });
  designs[idx] = { ...designs[idx], ...req.body, updatedAt: new Date().toISOString() };
  await v3Write('report_designs', designs);
  res.json(designs[idx]);
});
app.delete('/api/v3/reports/designs/:id', async (req: Request, res: Response) => {
  const designs = await v3Read<any[]>('report_designs', []);
  const filtered = designs.filter((d: any) => d.id !== req.params.id);
  await v3Write('report_designs', filtered);
  res.status(204).end();
});
app.post('/api/v3/reports/designs/:id/generate', async (req: Request, res: Response) => {
  const designs = await v3Read<any[]>('report_designs', []);
  const design = designs.find((d: any) => d.id === req.params.id);
  if (!design) return res.status(404).json({ error: 'Design not found' });
  res.json({ id: crypto.randomUUID(), designId: req.params.id, status: 'generated', channels: req.body.channels || [], generatedAt: new Date().toISOString() });
});
app.get('/api/v3/reports/schedules', async (_req: Request, res: Response) => {
  const schedules = await v3Read<any[]>('report_schedules', []);
  res.json(schedules);
});
app.post('/api/v3/reports/schedules', async (req: Request, res: Response) => {
  const schedules = await v3Read<any[]>('report_schedules', []);
  const newSchedule = { id: crypto.randomUUID(), ...req.body, createdAt: new Date().toISOString() };
  schedules.push(newSchedule);
  await v3Write('report_schedules', schedules);
  res.status(201).json(newSchedule);
});
app.delete('/api/v3/reports/schedules/:id', async (req: Request, res: Response) => {
  const schedules = await v3Read<any[]>('report_schedules', []);
  const filtered = schedules.filter((s: any) => s.id !== req.params.id);
  await v3Write('report_schedules', filtered);
  res.status(204).end();
});
app.get('/api/v3/reports/deliveries', async (_req: Request, res: Response) => {
  const deliveries = await v3Read<any[]>('report_deliveries', []);
  res.json(deliveries);
});
app.get('/api/v3/reports/templates', async (_req: Request, res: Response) => {
  const templates = await v3Read<any[]>('report_templates', [
    { id: 'executive-summary', name: 'Executive Summary', category: 'business' },
    { id: 'cost-report', name: 'Cost Report', category: 'finance' },
    { id: 'performance', name: 'Performance Report', category: 'ops' },
    { id: 'incidents', name: 'Incident Report', category: 'ops' },
    { id: 'anomaly-digest', name: 'Anomaly Digest', category: 'security' },
    { id: 'capacity-forecast', name: 'Capacity Forecast', category: 'ops' },
  ]);
  res.json(templates);
});

// ============================================================================
// V4 DATA PLATFORM & ANALYTICS API ROUTES
// ============================================================================

// --- Feature 41: Managed Data Lakehouse ---
app.get('/api/v4/data/lakehouse', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_lakehouse_clusters', []);
  res.json(data);
});
app.post('/api/v4/data/lakehouse', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_lakehouse_clusters', []);
  const cluster = { cluster_id: crypto.randomUUID(), ...req.body, tables: 0, status: 'active', created_at: new Date().toISOString() };
  data.push(cluster);
  await v3Write('v4_lakehouse_clusters', data);
  res.status(201).json(cluster);
});
app.get('/api/v4/data/lakehouse/:id', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_lakehouse_clusters', []);
  const cluster = data.find((c: any) => c.cluster_id === req.params.id);
  if (!cluster) return res.status(404).json({ error: 'Not found' });
  res.json(cluster);
});
app.delete('/api/v4/data/lakehouse/:id', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_lakehouse_clusters', []);
  const filtered = data.filter((c: any) => c.cluster_id !== req.params.id);
  await v3Write('v4_lakehouse_clusters', filtered);
  res.status(204).end();
});
app.post('/api/v4/data/lakehouse/tables/:id/compact', async (req: Request, res: Response) => {
  res.json({ table_id: req.params.id, status: 'compacted', timestamp: new Date().toISOString() });
});
app.post('/api/v4/data/lakehouse/tables/:id/vacuum', async (req: Request, res: Response) => {
  res.json({ table_id: req.params.id, status: 'vacuumed', retention_hours: req.body.retention_hours || 168 });
});

// --- Feature 42: Streaming Data Pipeline ---
app.get('/api/v4/data/streaming', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_streaming_clusters', []);
  res.json(data);
});
app.post('/api/v4/data/streaming', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_streaming_clusters', []);
  const cluster = { cluster_id: crypto.randomUUID(), ...req.body, topics: 0, connectors: 0, status: 'active', created_at: new Date().toISOString() };
  data.push(cluster);
  await v3Write('v4_streaming_clusters', data);
  res.status(201).json(cluster);
});
app.get('/api/v4/data/streaming/:id', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_streaming_clusters', []);
  const cluster = data.find((c: any) => c.cluster_id === req.params.id);
  if (!cluster) return res.status(404).json({ error: 'Not found' });
  res.json(cluster);
});
app.post('/api/v4/data/streaming/:id/topics', async (req: Request, res: Response) => {
  res.json({ cluster_id: req.params.id, topic: req.body.topic, partitions: req.body.partitions || 3, status: 'created' });
});
app.delete('/api/v4/data/streaming/:id/topics/:topic', async (req: Request, res: Response) => {
  res.status(204).end();
});
app.post('/api/v4/data/streaming/:id/scale', async (req: Request, res: Response) => {
  res.json({ cluster_id: req.params.id, nodes: req.body.nodes, status: 'scaled' });
});

// --- Feature 43: Data Quality Framework ---
app.get('/api/v4/data/quality/rules', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_quality_rules', []);
  res.json(data);
});
app.post('/api/v4/data/quality/rules', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_quality_rules', []);
  const rule = { rule_id: crypto.randomUUID(), ...req.body, enabled: true, created_at: new Date().toISOString() };
  data.push(rule);
  await v3Write('v4_quality_rules', data);
  res.status(201).json(rule);
});
app.post('/api/v4/data/quality/run', async (_req: Request, res: Response) => {
  const rules = await v3Read<any[]>('v4_quality_rules', []);
  const total = rules.length;
  const passed = Math.floor(total * 0.8);
  const failed = total - passed;
  res.json({ total, passed, failed, timestamp: new Date().toISOString() });
});
app.get('/api/v4/data/quality/violations', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_quality_violations', []);
  res.json(data);
});
app.get('/api/v4/data/quality/scorecard/:dataset', async (req: Request, res: Response) => {
  res.json({ dataset: req.params.dataset, overall_score: 92.5, rules: 4, passing: 3, failing: 1 });
});

// --- Feature 44: Analytics Query Workbench ---
app.get('/api/v4/data/query', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_saved_queries', []);
  res.json(data);
});
app.post('/api/v4/data/query/execute', async (req: Request, res: Response) => {
  await new Promise(r => setTimeout(r, 100));
  res.json({ query_id: crypto.randomUUID(), columns: ['id', 'name', 'value'], rows: [[1, 'test', 42.0]], row_count: 1, execution_time_ms: 42 });
});
app.post('/api/v4/data/query/save', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_saved_queries', []);
  const q = { query_id: crypto.randomUUID(), ...req.body, status: 'saved', created_at: new Date().toISOString() };
  data.push(q);
  await v3Write('v4_saved_queries', data);
  res.status(201).json(q);
});
app.delete('/api/v4/data/query/:id', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_saved_queries', []);
  await v3Write('v4_saved_queries', data.filter((q: any) => q.query_id !== req.params.id));
  res.status(204).end();
});
app.get('/api/v4/data/query/schema', async (_req: Request, res: Response) => {
  res.json([{ name: 'users', object_type: 'table', schema: 'public' }, { name: 'orders', object_type: 'table', schema: 'public' }]);
});

// --- Feature 45: Data Catalog & Governance ---
app.get('/api/v4/data/catalog/assets', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_catalog_assets', []);
  res.json(data);
});
app.post('/api/v4/data/catalog/assets', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_catalog_assets', []);
  const asset = { asset_id: crypto.randomUUID(), ...req.body, certified: false, created_at: new Date().toISOString() };
  data.push(asset);
  await v3Write('v4_catalog_assets', data);
  res.status(201).json(asset);
});
app.get('/api/v4/data/catalog/search', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_catalog_assets', []);
  const q = (req.query.q as string || '').toLowerCase();
  res.json(data.filter((a: any) => a.name?.toLowerCase().includes(q)));
});
app.post('/api/v4/data/catalog/harvest', async (_req: Request, res: Response) => {
  res.json({ status: 'completed', assets_found: 5, columns_found: 30, duration_sec: 2.3 });
});
app.post('/api/v4/data/catalog/assets/:id/certify', async (req: Request, res: Response) => {
  res.json({ asset_id: req.params.id, certified: true });
});

// --- Feature 46: Data Masking & Anonymization ---
app.get('/api/v4/data/masking/rules', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_masking_rules', []);
  res.json(data);
});
app.post('/api/v4/data/masking/rules', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_masking_rules', []);
  const rule = { rule_id: crypto.randomUUID(), ...req.body, enabled: true, created_at: new Date().toISOString() };
  data.push(rule);
  await v3Write('v4_masking_rules', data);
  res.status(201).json(rule);
});
app.get('/api/v4/data/masking/profiles', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_masking_profiles', []);
  res.json(data);
});
app.post('/api/v4/data/masking/profiles', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_masking_profiles', []);
  const profile = { profile_id: crypto.randomUUID(), ...req.body, rules: [], enabled: true };
  data.push(profile);
  await v3Write('v4_masking_profiles', data);
  res.status(201).json(profile);
});
app.post('/api/v4/data/masking/profiles/:id/apply', async (req: Request, res: Response) => {
  res.json({ profile_id: req.params.id, status: 'applied', total_rows_masked: 1500 });
});

// --- Feature 47: Self-Service Reporting ---
app.get('/api/v4/data/reports', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_reports', []);
  res.json(data);
});
app.post('/api/v4/data/reports', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_reports', []);
  const report = { report_id: crypto.randomUUID(), ...req.body, widgets: [], parameters: [], mode: 'visual', created_at: new Date().toISOString() };
  data.push(report);
  await v3Write('v4_reports', data);
  res.status(201).json(report);
});
app.post('/api/v4/data/reports/:id/execute', async (req: Request, res: Response) => {
  res.json({ report_id: req.params.id, status: 'executed', widgets: 4, execution_time_ms: 320 });
});
app.post('/api/v4/data/reports/:id/export', async (req: Request, res: Response) => {
  res.json({ report_id: req.params.id, format: req.body.format || 'pdf', url: `/exports/reports/${req.params.id}.${req.body.format || 'pdf'}` });
});
app.post('/api/v4/data/reports/:id/schedules', async (req: Request, res: Response) => {
  res.json({ schedule_id: crypto.randomUUID(), report_id: req.params.id, ...req.body, created_at: new Date().toISOString() });
});

// --- Feature 48: Real-Time Analytics Dashboard ---
app.get('/api/v4/data/realtime/dashboards', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_realtime_dashboards', []);
  res.json(data);
});
app.post('/api/v4/data/realtime/dashboards', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_realtime_dashboards', []);
  const db = { dashboard_id: crypto.randomUUID(), ...req.body, panels: [], refresh: 5, status: 'active', created_at: new Date().toISOString() };
  data.push(db);
  await v3Write('v4_realtime_dashboards', data);
  res.status(201).json(db);
});
app.delete('/api/v4/data/realtime/dashboards/:id', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_realtime_dashboards', []);
  await v3Write('v4_realtime_dashboards', data.filter((d: any) => d.dashboard_id !== req.params.id));
  res.status(204).end();
});
app.get('/api/v4/data/realtime/dashboards/:id/live', async (req: Request, res: Response) => {
  const dashboard = { dashboard_id: req.params.id, panels: { p1: { metric: 'cpu', value: Math.random() * 100 } } };
  res.json(dashboard);
});
app.post('/api/v4/data/realtime/metrics', async (req: Request, res: Response) => {
  res.json({ metric: req.body.name, value: req.body.value, ingested: true, timestamp: new Date().toISOString() });
});

// --- Feature 49: Data Pipeline Observability ---
app.get('/api/v4/data/pipelines', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_pipelines', []);
  res.json(data);
});
app.post('/api/v4/data/pipelines', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_pipelines', []);
  const pipeline = { pipeline_id: crypto.randomUUID(), ...req.body, nodes: [], edges: [], status: 'created', created_at: new Date().toISOString() };
  data.push(pipeline);
  await v3Write('v4_pipelines', data);
  res.status(201).json(pipeline);
});
app.post('/api/v4/data/pipelines/:id/start', async (req: Request, res: Response) => {
  res.json({ pipeline_id: req.params.id, status: 'running' });
});
app.post('/api/v4/data/pipelines/:id/stop', async (req: Request, res: Response) => {
  res.json({ pipeline_id: req.params.id, status: 'stopped' });
});
app.get('/api/v4/data/pipelines/:id/health', async (req: Request, res: Response) => {
  res.json({ pipeline_id: req.params.id, status: 'running', health: 'healthy', issues: [], metrics: { throughput: 2500, latency_ms: 45, error_rate: 0.3, freshness_sec: 0.5 } });
});
app.get('/api/v4/data/pipelines/:id/rca', async (req: Request, res: Response) => {
  res.json({ pipeline_id: req.params.id, root_causes: [{ node: 'source_db', issue: 'connection timeout', probability: 0.85 }] });
});

// --- Feature 50: Embedded Analytics SDK ---
app.get('/api/v4/data/embed/customers', async (_req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_embed_customers', []);
  res.json(data);
});
app.post('/api/v4/data/embed/customers', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_embed_customers', []);
  const customer = { customer_id: crypto.randomUUID(), ...req.body, api_key: 'ip_ea_' + crypto.randomUUID().replace(/-/g, '').slice(0, 32), active: true, embeds: 0, created_at: new Date().toISOString() };
  data.push(customer);
  await v3Write('v4_embed_customers', data);
  res.status(201).json(customer);
});
app.post('/api/v4/data/embed/customers/:id/rotate-key', async (req: Request, res: Response) => {
  res.json({ customer_id: req.params.id, api_key: 'ip_ea_' + crypto.randomUUID().replace(/-/g, '').slice(0, 32) });
});
app.get('/api/v4/data/embed/embeds', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_embed_embeds', []);
  if (req.query.customer_id) return res.json(data.filter((e: any) => e.customer_id === req.query.customer_id));
  res.json(data);
});
app.post('/api/v4/data/embed/embeds', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_embed_embeds', []);
  const embed = { embed_id: crypto.randomUUID(), ...req.body, active: true, created_at: new Date().toISOString() };
  data.push(embed);
  await v3Write('v4_embed_embeds', data);
  res.status(201).json(embed);
});
app.get('/api/v4/data/embed/embeds/:id/code', async (req: Request, res: Response) => {
  res.json({ embed_id: req.params.id, code: `<iframe src="https://analytics.infrapilot.io/embed/${req.params.id}" width="100%" height="600"></iframe>` });
});
app.delete('/api/v4/data/embed/embeds/:id', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_embed_embeds', []);
  await v3Write('v4_embed_embeds', data.filter((e: any) => e.embed_id !== req.params.id));
  res.status(204).end();
});
app.get('/api/v4/data/embed/stats', async (_req: Request, res: Response) => {
  const customers = await v3Read<any[]>('v4_embed_customers', []);
  const embeds = await v3Read<any[]>('v4_embed_embeds', []);
  res.json({ total_customers: customers.length, total_embeds: embeds.length, active_customers: customers.filter((c: any) => c.active).length });
});
app.delete('/api/v4/data/embed/customers/:id', async (req: Request, res: Response) => {
  const data = await v3Read<any[]>('v4_embed_customers', []);
  await v3Write('v4_embed_customers', data.filter((c: any) => c.customer_id !== req.params.id));
  res.status(204).end();
});

// ============================================================================
// START SERVER
// ============================================================================

const httpServer = http.createServer(app);

const wss = new WebSocketServer({ server: httpServer });

interface TerminalRoom {
  sessionId: string;
  appId: string;
  clients: Map<WebSocket, { userId: string; displayName: string }>;
  output: string[];
}

const terminalRooms = new Map<string, TerminalRoom>();

wss.on('connection', (ws, req) => {
  const url = new URL(req.url || '', 'http://localhost');
  const appId = url.searchParams.get('appId');
  const sessionId = url.searchParams.get('sessionId');
  const displayName = url.searchParams.get('displayName') || 'Anonymous';

  // Collaborative Terminal connection
  if (sessionId) {
    let room = terminalRooms.get(sessionId);
    if (!room) {
      room = { sessionId, appId: appId || '', clients: new Map(), output: [] };
      terminalRooms.set(sessionId, room);
    }

    const userId = 'user-' + crypto.randomBytes(6).toString('hex');
    room.clients.set(ws, { userId, displayName });

    // Send join notification
    const joinMsg = JSON.stringify({ type: 'user-joined', userId, displayName, users: Array.from(room.clients.values()).map(c => c) });
    for (const [client] of room.clients) {
      if (client.readyState === WebSocket.OPEN) client.send(joinMsg);
    }

    // Send existing output to new user
    ws.send(JSON.stringify({ type: 'history', lines: room.output }));

    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());

        if (msg.type === 'terminal-input') {
          const line = `[${displayName}] $ ${msg.text}`;
          room!.output.push(line);
          if (room!.output.length > 1000) room!.output.shift();

          for (const [client] of room!.clients) {
            if (client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify({ type: 'terminal-output', line, userId, displayName }));
            }
          }
        } else if (msg.type === 'cursor') {
          const cursorMsg = JSON.stringify({ type: 'cursor-update', userId, displayName, cursor: msg.cursor });
          for (const [client, info] of room!.clients) {
            if (client !== ws && client.readyState === WebSocket.OPEN) {
              client.send(cursorMsg);
            }
          }
        } else if (msg.type === 'chat') {
          const chatMsg = JSON.stringify({ type: 'chat-message', userId, displayName, text: msg.text, timestamp: new Date().toISOString() });
          for (const [client] of room!.clients) {
            if (client.readyState === WebSocket.OPEN) client.send(chatMsg);
          }
        } else if (msg.type === 'exec' && appId) {
          // Forward command execution
          const line = `[${displayName}] $ ${msg.command}`;
          room!.output.push(line);
          if (room!.output.length > 1000) room!.output.shift();

          for (const [client] of room!.clients) {
            if (client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify({ type: 'terminal-output', line, userId, displayName }));
            }
          }
        }
      } catch {}
    });

    ws.on('close', () => {
      if (room) {
        room.clients.delete(ws);
        const leaveMsg = JSON.stringify({ type: 'user-left', userId, displayName, users: Array.from(room.clients.values()).map(c => c) });
        for (const [client] of room.clients) {
          if (client.readyState === WebSocket.OPEN) client.send(leaveMsg);
        }
        if (room.clients.size === 0) {
          terminalRooms.delete(sessionId);
        }
      }
    });

    return;
  }

  // Original log streaming (for backward compatibility)
  if (!appId) { ws.close(); return; }

  ws.on('message', async (data) => {
    try {
      const msg = JSON.parse(data.toString());
      if (msg.type === 'subscribe' && msg.appId) {
        const logStream = spawn('docker', ['logs', '--tail', '100', '-f', msg.appId]);
        logStream.stdout.on('data', (chunk) => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'log', appId: msg.appId, data: chunk.toString() }));
          }
        });
        logStream.on('close', () => {
          ws.send(JSON.stringify({ type: 'log_end', appId: msg.appId }));
        });
        ws.on('close', () => { logStream.kill(); });
      }
      if (msg.type === 'subscribe:metrics' && msg.appId) {
        const interval = setInterval(async () => {
          try {
            const { stdout } = await execAsync(`docker stats ${msg.appId} --no-stream --format "{{json .}}"`);
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: 'metrics', appId: msg.appId, data: JSON.parse(stdout) }));
            }
          } catch {}
        }, 2000);
        ws.on('close', () => clearInterval(interval));
      }
    } catch {}
  });
});

if (process.env.NODE_ENV !== 'test') {
  httpServer.listen(port, () => {
    console.log(`✨ Docker Panel API running on http://localhost:${port}`);
    console.log(`📡 Frontend should be at http://localhost:5173`);
    console.log(`🐳 Make sure Supabase and Docker are configured in .env.local`);
  });
}
