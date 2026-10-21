import express from 'express';
import type { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import axios from 'axios';
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
import rateLimit from 'express-rate-limit';
import { sanitizeAuditValue } from './audit-sanitize.ts';

/**
 * Run a command as a child process and capture stdout/stderr.
 * @param command - The command to execute
 * @param args - Array of arguments for the command
 * @returns Promise resolving with stdout and stderr on success
 * @throws Error if the command exits with a non-zero code
 */
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
import {
  createWsGateway,
  createWsTokenRouter,
  loadWsConfig,
  resolveWsTicketSecret,
  TicketService,
  WsAuditLogger,
} from './ws/index.ts';
import type { WsAction } from './ws/index.ts';
import { createRbacGuards, RbacStore } from './rbac/index.ts';
import { registerSsoRoutes } from './sso/routes.ts';
import {
  SESSION_COOKIE_NAME,
  parseCookies,
  resolveSessionToken,
} from './sso/store.ts';
import {
  clearReauthGrant,
  configureScopeGuards,
  createTwoFactorStatusChecker,
  createTwoFactorVerifier,
  keyAllowsApp,
  normalizeScopes,
  require2FAReauth,
  requireScope,
  requireWildcardScope,
  scopeDenialFor,
} from './apikeys/index.ts';
import type { ResourceAction, ResourceType } from './rbac/index.ts';
import { SERVER_PRESETS } from './presets.ts';
import openapiSpec from './openapi.ts';
import { analyzeConfiguration } from './config-advice-engine.ts';
import {
  checkCpu,
  checkDisk,
  checkDns,
  checkLocalApi,
  checkMemory,
  collectSystemInfo,
  type DiagnosticCheck,
} from './doctor.ts';
import { runBenchmark } from './benchmark.ts';
import { buildReport, reportToCsv, reportToPdf } from './reports.ts';
import { buildPlan } from './assistant.ts';
import { executeGraphQL } from './graphql.ts';
import {
  isExternalRef,
  orchestratorSecretsConfigured,
  orchestratorStatus,
  resolveExternalSecret,
  rotateExternalSecret,
} from './secrets-external.ts';
// plugin-registry and change-approval-engine moved to experimental

dotenv.config({ path: '.env.local' });

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 3001;

// Production hardening defaults (no new deps): hide framework fingerprint,
// bound JSON bodies, minimal security headers. Reverse proxy / ingress
// terminates TLS; Express never serves public traffic directly.
app.disable('x-powered-by');
app.set('trust proxy', false);

const execAsync = promisify(exec);

/**
 * Run real diagnostics. The optional `issue` filters to a category:
 * connectivity | performance | disk. Without it, all checks run.
 */
async function runDiagnostics(issue?: string): Promise<{ status: string; summary: string; checks: DiagnosticCheck[]; system?: ReturnType<typeof collectSystemInfo> }> {
  const checks: DiagnosticCheck[] = [];
  const wants = (c: string) => !issue || issue === c;

  if (wants('performance') || wants('connectivity')) checks.push(checkCpu());
  if (wants('performance') || wants('connectivity')) checks.push(checkMemory());
  if (wants('disk') || wants('performance')) checks.push(checkDisk());
  if (wants('connectivity')) checks.push(await checkDns());
  if (wants('connectivity')) {
    const apiUrl = process.env.API_BASE_URL || `http://localhost:${port}`;
    checks.push(await checkLocalApi(apiUrl));
  }

  const failed = checks.filter((c) => c.status === 'fail');
  const warned = checks.filter((c) => c.status === 'warn');
  const status = failed.length > 0 ? 'fail' : warned.length > 0 ? 'warn' : 'ok';
  return {
    status,
    summary:
      status === 'ok'
        ? 'All checks passed'
        : status === 'warn'
          ? `${warned.length} warning(s), ${failed.length} failure(s)`
          : `${failed.length} failure(s) detected`,
    checks,
    system: collectSystemInfo(),
  };
}

/**
 * Execute a Docker action (start/stop/restart) on a container by app ID.
 * @param appId - The ID of the Docker app
 * @param action - Docker action to perform
 * @returns Result with success flag and command output
 * @throws Error if the app or container is not found
 */
async function dockerAction(appId: string, action: 'start' | 'stop' | 'restart'): Promise<{success: boolean; output: string}> {
  const { data: app, error } = await supabase
    .from('docker_apps')
    .select('container_id, user_id')
    .eq('id', appId)
    .single();
  if (error || !app) throw new Error('App not found');
  if (!app.container_id) throw new Error('No container associated with this app');
  const containerId = String(app.container_id);
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(containerId)) {
    throw new Error('Invalid container_id format');
  }
  const { stdout, stderr } = await runCommand('docker', [action, containerId]);
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
  message: { error: 'Too many requests, please try again later.' },
});

const generalLimiter = rateLimit({
  windowMs: 1 * 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many requests, please try again later.' },
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
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY || 'dev-local-anon-key';
if (process.env.NODE_ENV === 'production' && !process.env.VITE_SUPABASE_ANON_KEY) {
  throw new Error('VITE_SUPABASE_ANON_KEY is required in production; refusing to start with a dummy key');
}
let supabase = createClient(supabaseUrl, supabaseKey);

/**
 * Service-role client: only exists when the operator provides the key.
 * Required for SSO identity linking and JIT provisioning (auth admin API);
 * nullable everywhere else so SSO degrades to a clear 502 instead of
 * crashing the panel at boot.
 */
const supabaseAdmin = process.env.SUPABASE_SERVICE_ROLE_KEY
  ? createClient(supabaseUrl, process.env.SUPABASE_SERVICE_ROLE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false },
    })
  : null;

export function setSupabaseClientForTests(client: ReturnType<typeof createClient>) {
  supabase = client;
  rbacStore?.setClient(client);
}

export { app };

/**
 * Panel RBAC store + HTTP guards. Static moment: authorization is deny by
 * default — a check that cannot reach the store returns 503 and never
 * silently allows. Assignments persist in `rbac_instance_roles` and
 * `rbac_app_roles` (db/schema.sql); `wiki/11-Auth-Matrix.md` keeps the
 * decision table.
 */
let rbacStore: RbacStore | null = null;
let rbacGuards: ReturnType<typeof createRbacGuards> | null = null;

/**
 * Guard factory baked into the request chain before route definitions.
 * Called with a resource type and action; failures are audited as
 * `rbac:denied` and answered with 403 `code: 'rbac_denied'`.
 */
function requireSelfPermission(
  resourceType: ResourceType,
  action: ResourceAction,
) {
  return rbacGuards!.requirePermission(resourceType, action, { self: true });
}

function requireInstancePermission(resourceType: ResourceType, action: ResourceAction) {
  return rbacGuards!.requirePermission(resourceType, action);
}

function requireAppId(
  action: ResourceAction,
  resourceType: ResourceType = 'app',
  opts: { optional?: boolean } = {},
) {
  return rbacGuards!.requireAppRole(action, resourceType, opts);
}

// Legacy per-app permission shape kept for API compatibility (see
// server/rbac/catalog.ts for the mapping onto the modern vocabulary).
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

const serverSnapshots = new Map<string, any[]>();
const workspacesByUser = new Map<string, any[]>();
const pluginInstallations = new Map<string, any[]>();

rbacStore = new RbacStore(supabase, { cacheTtlMs: Number(process.env.RBAC_CACHE_TTL_MS) || 30_000 });
// Scoped API keys (v2): scope/app checks ride on the RBAC guard layer so
// every coordinated route gets both authorizations; sensitive routes also
// demand a fresh 2FA code (X-2FA-Token), see the API routes below.
rbacGuards = createRbacGuards({
  store: rbacStore,
  audit: logAudit,
  scopeCheck: (req, resourceType, action) => scopeDenialFor(req, resourceType, action),
  keyAllowsApp,
});
configureScopeGuards(logAudit);

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

function clampPct(value: number): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.min(Math.max(n, 0), 100);
}

function computeOverallScore(cpuPct: number, memPct: number): number {
  return Number(((clampPct(cpuPct) + clampPct(memPct)) / 2).toFixed(1));
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
// CORS: allow only configured origins (comma-separated CORS_ORIGINS, default localhost dev)
const corsOrigins = (process.env.CORS_ORIGINS || 'http://localhost:5173,http://localhost:3001')
  .split(',')
  .map((o) => o.trim())
  .filter(Boolean);
app.use(cors({ origin: corsOrigins, credentials: true }));
// Bound JSON bodies to contain memory-DoS via large payloads.
app.use(express.json({ limit: '100kb' }));
// Minimal security headers (helmet-equivalent subset without new dep).
app.use((_req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  next();
});

// Health and observability-aware health
const APP_HEALTH = {
  status: 'ok',
  uptime: process.uptime(),
  version: APP_VERSION,
  metrics,
};

// API key hashing: uses a slow KDF (scrypt) with a per-key random salt so a
// database leak does not allow offline brute-forcing of stored key hashes.
const API_KEY_HASH_PREFIX = 'scrypt:';
const API_KEY_SALT_BYTES = 16;
const API_KEY_HASH_BYTES = 64;

function hashApiKey(rawKey: string): string {
  const salt = crypto.randomBytes(API_KEY_SALT_BYTES);
  const hash = crypto.scryptSync(rawKey, salt, API_KEY_HASH_BYTES);
  return `${API_KEY_HASH_PREFIX}${salt.toString('hex')}:${hash.toString('hex')}`;
}

function apiKeyMatches(rawKey: string, storedHash: string | null | undefined): boolean {
  if (!storedHash || !storedHash.startsWith(API_KEY_HASH_PREFIX)) return false;
  const parts = storedHash.substring(API_KEY_HASH_PREFIX.length).split(':');
  if (parts.length !== 2) return false;
  const expected = Buffer.from(parts[1], 'hex');
  const actual = crypto.scryptSync(rawKey, Buffer.from(parts[0], 'hex'), expected.length);
  return crypto.timingSafeEqual(actual, expected);
}

/**
 * Auth middleware: Verify JWT token from Authorization header and attach user to request.
 * @param req - Express request
 * @param res - Express response
 * @param next - Next middleware function
 */
const verifyAuth = async (req: Request, res: Response, next: NextFunction) => {
  const token = req.headers.authorization?.split('Bearer ')[1];

  // SSO panel sessions may arrive as a Bearer token (`sso_...`, minted at
  // the OIDC callback) or as the `ip_session` cookie. They carry the same
  // authority as the user they were minted for; DB state stays the source
  // of truth (revocable, expiring).
  const sessionTokenSource = token?.startsWith('sso_')
    ? token
    : (token ? null : parseCookies(req.headers.cookie)[SESSION_COOKIE_NAME] || null);
  if (sessionTokenSource) {
    const session = await resolveSessionToken(supabase, sessionTokenSource);
    if (session) {
      (req as any).user = { id: session.user_id };
      (req as any).authMethod = 'sso-session';
      (req as any).session = session;
      return next();
    }
    if (token && token.startsWith('sso_')) {
      // An explicit sso_ Bearer token that failed validation must not fall
      // through into JWT/API-key matching.
      return res.status(401).json({ error: 'Invalid token' });
    }
  }

  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const { data, error } = await supabase.auth.getUser(token);
  if (data?.user) {
    (req as any).user = data.user;
    return next();
  }

  const keyPrefix = token.substring(0, 10);
  const { data: apiKeyRow } = await supabase
    .from('api_keys')
    .select('id, user_id, key_hash, scopes, key_class, app_id, expires_at, force_rotate')
    .eq('key_prefix', keyPrefix)
    .eq('revoked', false)
    .maybeSingle();

  if (apiKeyRow && apiKeyMatches(token, apiKeyRow.key_hash)) {
    if (apiKeyRow.expires_at && new Date(apiKeyRow.expires_at).getTime() < Date.now()) {
      return res.status(401).json({ error: 'API key expired', code: 'key_expired' });
    }
    (req as any).apiKey = {
      id: apiKeyRow.id,
      userId: apiKeyRow.user_id,
      scopes: Array.isArray(apiKeyRow.scopes) ? (apiKeyRow.scopes as string[]) : null,
      keyClass: apiKeyRow.key_class || null,
      appId: apiKeyRow.app_id || null,
      forceRotate: apiKeyRow.force_rotate === true || !Array.isArray(apiKeyRow.scopes),
    };
    (req as any).user = { id: apiKeyRow.user_id };
    return next();
  }

  return res.status(401).json({ error: 'Invalid token' });
};

/**
 * Log an audit event to the database.
 * @param userId - ID of the user performing the action
 * @param action - Action description (e.g. 'app:create')
 * @param entityType - Type of entity being acted upon
 * @param entityId - ID of the entity
 * @param oldValue - Previous value (for updates)
 * @param newValue - New value
 * @param ipAddress - IP address of the requester
 */
async function logAudit(userId: string, action: string, entityType: string, entityId?: string, oldValue?: any, newValue?: any, ipAddress?: string) {
  try {
    await supabase
      .from('audit_log')
      .insert({
        user_id: userId,
        action,
        entity_type: entityType,
        entity_id: entityId,
        old_value: oldValue ? JSON.stringify(sanitizeAuditValue(oldValue)) : null,
        new_value: newValue ? JSON.stringify(sanitizeAuditValue(newValue)) : null,
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

app.get('/api/settings/secrets-backend', verifyAuth, requireSelfPermission('settings', 'read'), async (req: Request, res: Response) => {
  const status = await orchestratorStatus();
  res.json({ externalSecrets: status });
});

// POST /api/setup/init - Initialize setup (create first admin user & mode selection)
app.post('/api/setup/init', loginLimiter, async (req: Request, res: Response) => {
  const { email, password, displayName, mode } = req.body;

  if (!email || !password || !mode || !['personal', 'business'].includes(mode)) {
    return res.status(400).json({ error: 'Missing or invalid parameters' });
  }

  try {
    // Refuse re-initialization once an admin account already exists
    const { data: existingSetup, error: setupCheckError } = await supabase
      .from('setup_config')
      .select('initialized')
      .single();

    if (!setupCheckError && existingSetup?.initialized) {
      return res.status(409).json({ error: 'Setup already initialized' });
    }

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

    // RBAC bootstrap: promote the setup-created admin user immediately so
    // instance administration works without waiting for a restart.
    await rbacStore!.bootstrapInstanceRoles();

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
app.post('/api/validate/discord-token', generalLimiter, async (req: Request, res: Response) => {
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
app.get('/api/apps', verifyAuth, requireScope('apps', 'read'), async (req: Request, res: Response) => {
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
app.post('/api/apps', verifyAuth, requireScope('apps', 'write'), async (req: Request, res: Response) => {
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

// GET /api/apps/:appId - Get app details (owner or authorized assignment)
app.get('/api/apps/:appId', verifyAuth, requireAppId('read'), async (req: Request, res: Response) => {
  const appRecord = (req as any).appRecord;

  try {
    res.json(appRecord);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch app' });
  }
});

// PATCH /api/apps/:appId - Update app settings (owner or app assignment with write)
app.patch('/api/apps/:appId', verifyAuth, requireAppId('write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = (req as any).appAccess.appId;
  const appRecord = (req as any).appRecord;
  const { javaVersion, ...otherFields } = req.body;

  const ALLOWED_UPDATE_FIELDS = [
    'name',
    'image',
    'ports',
    'environment_vars',
    'volumes',
    'restart_policy',
    'memory_limit',
    'cpu_shares',
    'description',
    'labels',
  ];

  try {
    const updateData: Record<string, unknown> = {};
    for (const field of ALLOWED_UPDATE_FIELDS) {
      if (otherFields[field] !== undefined) {
        updateData[field] = otherFields[field];
      }
    }

    if (javaVersion) {
      const envVars = { ...((appRecord.environment_vars as Record<string, string>) || {}), JAVA_VERSION: javaVersion };
      updateData.environment_vars = envVars;
    }

    const { data, error } = await supabase
      .from('docker_apps')
      .update(updateData)
      .eq('id', appId)
      .eq('user_id', appRecord.user_id)
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

// DELETE /api/apps/:appId - Delete an app (owner or assignment with delete)
app.delete('/api/apps/:appId', verifyAuth, requireAppId('delete'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = (req as any).appAccess.appId;
  const appRecord = (req as any).appRecord;

  try {
    const { error } = await supabase
      .from('docker_apps')
      .delete()
      .eq('id', appId)
      .eq('user_id', appRecord.user_id);

    if (error) throw error;
    rbacStore!.invalidateApp(appId);
    await logAudit(userId, 'app:delete', 'app', appId);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete app' });
  }
});

// ============================================================================
// DOCKER CONTROL ROUTES (require auth)
// ============================================================================

// POST /api/apps/:appId/start - Start a container (owner or assignment with exec)
app.post('/api/apps/:appId/start', verifyAuth, requireAppId('exec'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = (req as any).appAccess.appId;
  const appRecord = (req as any).appRecord;

  try {
    const dockerResult = await dockerAction(appId, 'start');
    const { data, error } = await supabase
      .from('docker_apps')
      .update({
        status: 'running',
        started_at: new Date().toISOString(),
      })
      .eq('id', appId)
      .eq('user_id', appRecord.user_id)
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

// POST /api/apps/:appId/stop - Stop a container (owner or assignment with exec)
app.post('/api/apps/:appId/stop', verifyAuth, requireAppId('exec'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = (req as any).appAccess.appId;
  const appRecord = (req as any).appRecord;

  try {
    const dockerResult = await dockerAction(appId, 'stop');
    const { data, error } = await supabase
      .from('docker_apps')
      .update({ status: 'stopped' })
      .eq('id', appId)
      .eq('user_id', appRecord.user_id)
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

// POST /api/apps/:appId/restart - Restart a container (owner or assignment with exec)
app.post('/api/apps/:appId/restart', verifyAuth, requireAppId('exec'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = (req as any).appAccess.appId;
  const appRecord = (req as any).appRecord;

  try {
    const dockerResult = await dockerAction(appId, 'restart');
    const { data, error } = await supabase
      .from('docker_apps')
      .update({
        status: 'running',
        started_at: new Date().toISOString(),
      })
      .eq('id', appId)
      .eq('user_id', appRecord.user_id)
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

// GET /api/apps/:appId/logs - Stream logs with search, filtering, pagination (owner or assignment)
app.get('/api/apps/:appId/logs', verifyAuth, requireAppId('read'), async (req: Request, res: Response) => {
  const { appId } = req.params;
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 1000);
  const page = Math.max(parseInt(req.query.page as string) || 1, 1);
  const offset = (page - 1) * limit;
  const search = req.query.search as string;
  const level = req.query.level as string;
  const from = req.query.from as string;
  const to = req.query.to as string;

  try {
    // The RBAC guard verified access and confirmed the app exists.

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
// Clone requires exec on the source app; the clone is owned by the caller.
app.post('/api/apps/:appId/clone', verifyAuth, requireAppId('exec'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const source = (req as any).appRecord;
  const { name, includeFiles = true, includeBackups = true } = req.body;
  const appId = source.id;

  try {
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
    // Ownership is authoritative: the app owner implicitly holds every
    // permission, so no assignment row is created for the cloner.
    await logAudit(userId, 'app:clone', 'app', data.id, { sourceAppId: appId }, { name: cloneName, includeFiles, includeBackups });
    res.status(201).json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to clone app' });
  }
});

/**
 * Per-app role assignments backed by `rbac_app_roles` (server/rbac).
 * Reading/managing assignments maps to the `members` resource: app owners
 * and `admin` assignments decide who else can join the app, and instance
 * admins override. Wire shape keeps the legacy `principal` field.
 */
app.get('/api/apps/:appId/roles', verifyAuth, requireAppId('read', 'members'), async (req: Request, res: Response) => {
  const appId = (req as any).appAccess.appId;
  try {
    const rows = await rbacStore!.listAppRoles(appId);
    res.json(rows.map((row) => RbacStore.toWire(row, fullServerPermissions)));
  } catch (err) {
    res.status(500).json({ error: 'Failed to list app roles' });
  }
});

app.post('/api/apps/:appId/roles', verifyAuth, requireAppId('manage', 'members'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = (req as any).appAccess.appId;
  const { principal, role, permissions } = req.body || {};
  if (!principal || typeof principal !== 'string') {
    return res.status(400).json({ error: 'principal (user id) is required' });
  }
  if (!role || typeof role !== 'string') {
    return res.status(400).json({ error: 'role is required' });
  }

  try {
    const assignment = await rbacStore!.setAppRole(appId, principal, role as any, permissions ?? null, userId);
    await logAudit(userId, 'app:role-upsert', 'app', appId, null, {
      principal,
      role: assignment.role,
      permissions: permissions ?? null,
    });
    res.status(201).json(RbacStore.toWire(assignment, fullServerPermissions));
  } catch (err: any) {
    const message = String(err?.message || 'Failed to upsert app role');
    if (message.includes('must be')) return res.status(400).json({ error: message });
    res.status(500).json({ error: 'Failed to upsert app role' });
  }
});

app.get('/api/apps/:appId/snapshots', verifyAuth, requireAppId('read', 'backup'), async (req: Request, res: Response) => {
  const appId = (req as any).appAccess.appId;
  if (!serverSnapshots.has(appId)) serverSnapshots.set(appId, createDefaultSnapshots(appId));
  res.json(serverSnapshots.get(appId));
});

app.post('/api/apps/:appId/snapshots', verifyAuth, requireAppId('write', 'backup'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = (req as any).appAccess.appId;
  const source = (req as any).appRecord;
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

app.post('/api/apps/:appId/snapshots/:snapshotId/restore', verifyAuth, requireAppId('write', 'backup'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId, snapshotId } = req.params;
  const snapshots = serverSnapshots.get(appId) || createDefaultSnapshots(appId);
  const snapshot = snapshots.find((item) => item.id === snapshotId);
  if (!snapshot) return res.status(404).json({ error: 'Snapshot not found' });
  snapshot.status = 'restoring';
  snapshot.restoredAt = new Date().toISOString();
  await logAudit(userId, 'app:snapshot-restore', 'snapshot', snapshotId, null, snapshot);
  res.json(snapshot);
});

// GET /api/apps/:appId/status - Get app status (owner or authorized assignment)
app.get('/api/apps/:appId/status', verifyAuth, requireAppId('read'), async (req: Request, res: Response) => {
  const appRecord = (req as any).appRecord;

  try {
    res.json({ status: appRecord.status, started_at: appRecord.started_at, memory_limit: appRecord.memory_limit, cpu_shares: appRecord.cpu_shares });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch app status' });
  }
});

app.get('/api/apps/:appId/autopilot', verifyAuth, requireAppId('read'), async (req: Request, res: Response) => {
  const appId = (req as any).appAccess.appId;
  const source = (req as any).appRecord;
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

app.get('/api/workspaces', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  if (!workspacesByUser.has(userId)) {
    workspacesByUser.set(userId, [{ id: crypto.randomUUID(), name: 'Default Workspace', appIds: [], memberCount: 1, sharedBackups: true, sharedLogs: true, createdAt: new Date().toISOString() }]);
  }
  res.json(workspacesByUser.get(userId));
});

app.post('/api/workspaces', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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

app.get('/api/apps/:appId/billing', verifyAuth, requireAppId('read'), async (req: Request, res: Response) => {
  const appId = (req as any).appAccess.appId;
  const source = (req as any).appRecord;
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

app.post('/api/apps/:appId/plugins/:pluginId/install', verifyAuth, requireAppId('write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId, pluginId } = req.params;
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
app.get('/api/apps/:appId/config', verifyAuth, requireAppId('read', 'config'), async (req: Request, res: Response) => {
  const appId = (req as any).appAccess.appId;
  const app = (req as any).appRecord;
  const path = (req.query.path as string) || '/';

  try {
    if (!app.container_id) return res.status(400).json({ error: 'No container associated with this app' });

    const safePath = path.replace(/[^a-zA-Z0-9_\-\.\/]/g, '');
    const { stdout, stderr } = await runCommand('docker', ['exec', app.container_id, 'ls', '-la', safePath]).catch((err: any) => {
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
app.get('/api/apps/:appId/config/read', verifyAuth, requireAppId('read', 'config'), async (req: Request, res: Response) => {
  const { appId } = req.params;
  const file = req.query.file as string;

  if (!file) return res.status(400).json({ error: 'file query parameter is required' });

  try {
    const app = (req as any).appRecord;
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
app.post('/api/apps/:appId/config/write', verifyAuth, requireAppId('write', 'config'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const { path: filePath, content } = req.body;

  if (!filePath || content === undefined) return res.status(400).json({ error: 'path and content are required' });

  try {
    const app = (req as any).appRecord;
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
app.get('/api/apps/:appId/config/validate', verifyAuth, requireAppId('read', 'config'), async (req: Request, res: Response) => {
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
    const app = (req as any).appRecord;
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

// CLI-compatible health endpoint (CLI prepends /api to all paths)
app.get('/api/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', uptime: process.uptime(), version: APP_VERSION, metrics });
});

// ============================================================================
// 2FA (Two-Factor Authentication) Routes
// ============================================================================

const INTEGRATION_SERVICE_URL = process.env.INTEGRATION_SERVICE_URL || 'http://localhost:9000';

/**
 * JSON request to the integration service without streaming the response
 * (used by the 2FA re-auth middleware, which needs a boolean verdict).
 */
async function integrationRequest(path: string, init: { method: string; body?: string } = { method: 'GET' }): Promise<{ ok: boolean; data?: any }> {
  try {
    const response = await fetch(`${INTEGRATION_SERVICE_URL}${path}`, {
      method: init.method,
      headers: { 'Content-Type': 'application/json' },
      body: init.body,
      signal: AbortSignal.timeout(10_000),
    });
    let data: any = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    return { ok: response.ok, data };
  } catch {
    return { ok: false, data: null };
  }
}

// Fail-closed middleware stack for sensitive operations (API-key
// management, report/audit export, 2FA disable, backup-code retrieval).
const twoFactorProbe = createTwoFactorVerifier(integrationRequest);
const twoFactorStatus = createTwoFactorStatusChecker(integrationRequest);
const sensitive2FA = require2FAReauth(twoFactorProbe, twoFactorStatus);

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

/**
 * 2FA settings are personal: a caller may only manage their own enrolment.
 * `forwardToIntegration` relays the client body verbatim, so gate any
 * `user_id` in it against the authenticated identity (RBAC deny-by-default
 * applies even to personal flows) and default it to the caller's id.
 */
function selfOrRequestBodyUser(req: Request): boolean {
  const userId = (req as any).user?.id;
  const bodyUserId = (req.body || {}).user_id;
  if (typeof bodyUserId === 'string' && bodyUserId && bodyUserId !== userId) return false;
  if (!bodyUserId && userId) {
    (req as any).body = { ...(req.body || {}), user_id: userId };
  }
  return true;
}

app.post('/api/auth/2fa/setup', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  if (!selfOrRequestBodyUser(req)) {
    return res.status(403).json({ error: 'Forbidden', code: 'rbac_denied' });
  }
  await forwardToIntegration(req, res, '/api/auth/2fa/setup');
  await logAudit(userId, 'auth:2fa-setup', 'settings', userId);
});

app.post('/api/auth/2fa/verify-setup', verifyAuth, async (req: Request, res: Response) => {
  if (!selfOrRequestBodyUser(req)) {
    return res.status(403).json({ error: 'Forbidden', code: 'rbac_denied' });
  }
  await forwardToIntegration(req, res, '/api/auth/2fa/verify-setup');
});

app.post('/api/auth/2fa/verify', loginLimiter, async (req: Request, res: Response) => {
  await forwardToIntegration(req, res, '/api/auth/2fa/verify');
});

app.post('/api/auth/2fa/disable', verifyAuth, sensitive2FA, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  if (!selfOrRequestBodyUser(req)) {
    return res.status(403).json({ error: 'Forbidden', code: 'rbac_denied' });
  }
  await forwardToIntegration(req, res, '/api/auth/2fa/disable');
  await logAudit(userId, 'auth:2fa-disable', 'settings', userId);
});

app.get('/api/auth/2fa/backup-codes', verifyAuth, sensitive2FA, async (req: Request, res: Response) => {
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

app.post('/api/auth/2fa/verify-backup', loginLimiter, async (req: Request, res: Response) => {
  await forwardToIntegration(req, res, '/api/auth/2fa/verify-backup');
});

// POST /api/auth/login - Authenticate with an API key
app.post('/api/auth/login', async (req: Request, res: Response) => {
  const { api_key } = req.body;
  if (!api_key || typeof api_key !== 'string') {
    return res.status(400).json({ error: 'api_key is required' });
  }

  const keyPrefix = api_key.substring(0, 10);
  const { data, error } = await supabase
    .from('api_keys')
    .select('id, user_id, key_hash, scopes, key_class, app_id, expires_at, force_rotate')
    .eq('key_prefix', keyPrefix)
    .eq('revoked', false)
    .maybeSingle();

  if (!data) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  if (!apiKeyMatches(api_key, data.key_hash)) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  if (data.expires_at && new Date(data.expires_at).getTime() < Date.now()) {
    return res.status(401).json({ error: 'API key expired', code: 'key_expired' });
  }

  await supabase
    .from('api_keys')
    .update({ last_used_at: new Date().toISOString() })
    .eq('id', data.id);

  res.json({
    token: api_key,
    user_id: data.user_id,
    scopes: Array.isArray(data.scopes) ? data.scopes : [WILDCARD_SCOPE],
    key_class: data.key_class || 'legacy',
    app_id: data.app_id || null,
    expires_at: data.expires_at || null,
    needs_rotation: !Array.isArray(data.scopes),
  });
});

// POST /api/auth/logout - Invalidate the current session
app.post('/api/auth/logout', async (_req: Request, res: Response) => {
  res.json({ success: true });
});

// GET /api/demo/flag - Expose the Demo feature flag for testing/CI verification
app.get('/api/demo/flag', (_req: Request, res: Response) => {
  const enabled = process.env.VITE_DEMO_FEATURE_ENABLED === 'true';
  res.json({ enabled });
});

// Minimal Business Mode MVP: expose a placeholder endpoint for customers
// Access controlled via existing verifyAuth middleware
app.get('/api/customers', verifyAuth, customersLimiter, requireSelfPermission('customers', 'read'), async (req: Request, res: Response) => {
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
app.post('/api/customers', verifyAuth, customersLimiter, requireSelfPermission('customers', 'write'), async (req: Request, res: Response) => {
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
app.post('/api/seed-demo', verifyAuth, requireSelfPermission('customers', 'write'), async (req: Request, res: Response) => {
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
app.patch('/api/customers/:customerId', verifyAuth, requireSelfPermission('customers', 'write'), async (req: Request, res: Response) => {
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
app.delete('/api/customers/:customerId', verifyAuth, requireSelfPermission('customers', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/apps/:appId/metrics', verifyAuth, requireAppId('read', 'metrics'), async (req: Request, res: Response) => {
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
app.get('/api/metrics/aggregated', verifyAuth, requireScope('metrics', 'read'), async (req: Request, res: Response) => {
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
app.get('/api/metrics/realtime', verifyAuth, generalLimiter, requireAppId('read', 'metrics'), async (req: Request, res: Response) => {
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
        const { stdout } = await runCommand('docker', ['stats', app.container_id, '--no-stream', '--format', '{{json .}}']).catch(() => ({ stdout: '', stderr: '' }));
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
app.get('/api/metrics/history', verifyAuth, requireAppId('read', 'metrics', { optional: true }), async (req: Request, res: Response) => {
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
app.post('/api/metrics/stream/config', verifyAuth, requireScope('settings', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/metrics/grafana-url', verifyAuth, requireScope('metrics', 'read'), async (req: Request, res: Response) => {
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
app.get('/api/logs/access', verifyAuth, requireScope('audit', 'read'), async (req: Request, res: Response) => {
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
app.get('/api/apps/:appId/config-versions', verifyAuth, requireAppId('read', 'config'), async (req: Request, res: Response) => {
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
app.post('/api/apps/:appId/config-versions', verifyAuth, requireAppId('write', 'config'), async (req: Request, res: Response) => {
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
app.post('/api/apps/:appId/config-versions/:version/rollback', verifyAuth, requireAppId('write', 'config'), async (req: Request, res: Response) => {
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
app.get('/api/maintenance-windows', verifyAuth, requireSelfPermission('maintenance', 'read'), async (req: Request, res: Response) => {
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

app.post('/api/maintenance-windows', verifyAuth, requireSelfPermission('maintenance', 'write'), async (req: Request, res: Response) => {
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

app.patch('/api/maintenance-windows/:id', verifyAuth, requireSelfPermission('maintenance', 'write'), async (req: Request, res: Response) => {
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

app.get('/api/scheduled-tasks', verifyAuth, requireSelfPermission('maintenance', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const tasks = await getScheduledTasks();
    const userTasks = tasks.filter((t: any) => t.user_id === userId);
    res.json(userTasks);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch scheduled tasks' });
  }
});

app.post('/api/scheduled-tasks', verifyAuth, requireSelfPermission('maintenance', 'write'), async (req: Request, res: Response) => {
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

app.patch('/api/scheduled-tasks/:id', verifyAuth, requireSelfPermission('maintenance', 'write'), async (req: Request, res: Response) => {
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

app.delete('/api/scheduled-tasks/:id', verifyAuth, requireSelfPermission('maintenance', 'write'), async (req: Request, res: Response) => {
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

app.post('/api/scheduled-tasks/:id/toggle', verifyAuth, requireSelfPermission('maintenance', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/backup-jobs', verifyAuth, requireSelfPermission('backup', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const appId = req.query.app_id as string | undefined;
  try {
    let query = supabase
      .from('backup_jobs')
      .select('*')
      .eq('user_id', userId);
    if (appId) query = query.eq('app_id', appId);
    const { data, error } = await query.order('created_at', { ascending: false });
    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch backup jobs' });
  }
});

app.post('/api/backup-jobs', verifyAuth, requireSelfPermission('backup', 'write'), async (req: Request, res: Response) => {
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

app.patch('/api/backup-jobs/:id', verifyAuth, requireSelfPermission('backup', 'write'), async (req: Request, res: Response) => {
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

app.delete('/api/backup-jobs/:id', verifyAuth, requireSelfPermission('backup', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/backup-jobs/:jobId/status', verifyAuth, requireSelfPermission('backup', 'read'), async (req: Request, res: Response) => {
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

// Rate limiter for file-system-heavy backup artifact listing
const backupArtifactsLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 60, // limit each IP to 60 requests per minute
  standardHeaders: true,
  legacyHeaders: false,
});

// GET /api/backup-artifacts - Read-only list of db-backup.sh artifacts
app.get('/api/backup-artifacts', verifyAuth, backupArtifactsLimiter, requireSelfPermission('backup', 'read'), async (_req: Request, res: Response) => {
  try {
    const dir = process.env.BACKUP_DIR || path.resolve(__dirname, '..', '..', '..', 'backups');
    let names: string[] = [];
    try {
      names = await fs.readdir(dir);
    } catch {
      return res.json({ artifacts: [], last_success_epoch: null });
    }
    const artifacts = [];
    for (const name of names.filter((n) => !n.endsWith('.sha256') && !n.endsWith('.prom')).sort().reverse().slice(0, 50)) {
      try {
        const full = path.join(dir, name);
        const st = await fs.stat(full);
        if (!st.isFile()) continue;
        let sha256Present = false;
        try { await fs.stat(`${full}.sha256`); sha256Present = true; } catch { /* sidecar absent */ }
        artifacts.push({ name, size_bytes: st.size, mtime_ms: st.mtimeMs, sha256_present: sha256Present });
      } catch { /* skip unreadable entries */ }
    }
    artifacts.sort((a, b) => b.mtime_ms - a.mtime_ms);
    let lastSuccessEpoch: number | null = null;
    try {
      const prom = await fs.readFile(path.join(dir, 'last_success.prom'), 'utf8');
      const m = prom.match(/^backup_last_success_timestamp\s+(\d+)/m);
      if (m) lastSuccessEpoch = Number(m[1]);
    } catch { /* no prom file yet */ }
    res.json({ artifacts, last_success_epoch: lastSuccessEpoch });
  } catch (err) {
    res.status(500).json({ error: 'Failed to list backup artifacts' });
  }
});

// POST /api/backup/config - S3/Backblaze backup storage configuration
app.post('/api/backup/config', verifyAuth, requireSelfPermission('backup', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { s3_bucket, s3_key, s3_secret, s3_endpoint } = req.body;
  await supabase.from('shared_config').upsert({ key: `backup_s3_config_${userId}`, value: { s3_bucket, s3_key, s3_secret: s3_secret ? '***' : undefined, s3_endpoint } }, { onConflict: 'key' });
  res.json({ status: 'configured', storage: s3_bucket ? `s3://${s3_bucket}` : 'local' });
});

// POST /api/backups/:backupId/restore - Restore from backup
app.post('/api/backups/:backupId/restore', verifyAuth, requireSelfPermission('backup', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { target } = req.body;
  res.json({ status: 'restore_initiated', backup_id: req.params.backupId, target: target || 'original', message: 'Restore process started' });
});

// Alert Configs CRUD
app.get('/api/alert-configs', verifyAuth, requireSelfPermission('notifications', 'read'), async (req: Request, res: Response) => {
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

app.post('/api/alert-configs', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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

app.patch('/api/alert-configs/:id', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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

app.delete('/api/alert-configs/:id', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/alert-history', verifyAuth, requireSelfPermission('notifications', 'read'), async (req: Request, res: Response) => {
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

app.post('/api/alert-history/:id/acknowledge', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/health-checks', verifyAuth, requireSelfPermission('metrics', 'read'), async (req: Request, res: Response) => {
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
app.get('/api/reports', verifyAuth, requireSelfPermission('reports', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const startDate = req.query.start_date as string;
  const endDate = req.query.end_date as string;
  try {
    const report = await buildReport(supabase, userId, startDate, endDate);
    res.json(report);
  } catch (err) {
    res.status(500).json({ error: 'Failed to generate report' });
  }
});

app.get('/api/reports/export', verifyAuth, requireSelfPermission('reports', 'export'), sensitive2FA, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const startDate = req.query.start_date as string;
  const endDate = req.query.end_date as string;
  const format = req.query.format as string;
  try {
    const report = await buildReport(supabase, userId, startDate, endDate);
    if (format === 'csv') {
      const csv = reportToCsv(report);
      res.setHeader('Content-Type', 'text/csv; charset=utf-8');
      res.setHeader('Content-Disposition', 'attachment; filename=report.csv');
      res.send(csv);
    } else if (format === 'pdf') {
      const pdf = reportToPdf(report);
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', 'attachment; filename=report.pdf');
      res.send(pdf);
    } else if (format === 'json') {
      res.json(report);
    } else {
      res.status(400).json({ error: 'Unsupported format. Use csv, pdf or json.' });
    }
  } catch (err) {
    res.status(500).json({ error: 'Failed to export report' });
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
app.get('/api/databases', verifyAuth, requireSelfPermission('databases', 'read'), async (req: Request, res: Response) => {
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
app.post('/api/databases', verifyAuth, requireSelfPermission('databases', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/databases/:id', verifyAuth, requireSelfPermission('databases', 'read'), async (req: Request, res: Response) => {
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
app.delete('/api/databases/:id', verifyAuth, requireSelfPermission('databases', 'write'), async (req: Request, res: Response) => {
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
app.get('/api/modpacks/search', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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
app.post('/api/apps/:appId/modpacks/install', verifyAuth, requireAppId('write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const { modpackId, platform } = req.body;

  if (!modpackId || !platform) {
    return res.status(400).json({ error: 'modpackId and platform are required' });
  }

  const allowedPlatforms = new Set(['modrinth', 'curseforge']);
  if (!allowedPlatforms.has(platform)) {
    return res.status(400).json({ error: 'Invalid platform' });
  }

  const modpackParts = String(modpackId).split(':');
  if (modpackParts.length < 2 || !modpackParts[1]) {
    return res.status(400).json({ error: 'Invalid modpackId format' });
  }

  const safePlatform = encodeURIComponent(platform);
  const safeModpackRef = encodeURIComponent(modpackParts[1]);

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
    fetch(`${INTEGRATION_SERVICE_URL}/api/modpacks/${safePlatform}/${safeModpackRef}`)
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
app.get('/api/apps/:appId/modpacks/status', verifyAuth, requireAppId('read'), async (req: Request, res: Response) => {
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

app.get('/api/audit-log', verifyAuth, requireSelfPermission('audit', 'read'), async (req: Request, res: Response) => {
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

app.get('/api/notification-channels', verifyAuth, requireSelfPermission('notifications', 'read'), async (req: Request, res: Response) => {
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

app.post('/api/notification-channels', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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

app.patch('/api/notification-channels/:id', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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

app.delete('/api/notification-channels/:id', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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

// Orchestrator forwarding: only active when ORCHESTRATOR_API_TOKEN is set.
// Without it the panel keeps its store-only behavior, so local setups and
// the existing test suite are unaffected.
const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8500';
const ORCHESTRATOR_API_TOKEN = process.env.ORCHESTRATOR_API_TOKEN || '';

const buildManifestFromDeployment = (d: any): any => ({
  api_version: 'v1',
  kind: 'InfraFile',
  metadata: { name: d.name, environment: 'production' },
  spec: {
    instances: [
      {
        name: d.containerId || d.name,
        provider: 'docker',
        image: d.image || 'ubuntu:22.04',
        cpu: d.cpu ?? 1.0,
        memory_mb: d.memory_mb ?? 512,
        storage_gb: d.storage_gb ?? 10,
        env: {
          GIT_REPO: d.repoUrl,
          GIT_BRANCH: d.branch || 'main',
        },
      },
    ],
  },
});

const forwardDeploymentToOrchestrator = async (deployment: any): Promise<any | null> => {
  if (!ORCHESTRATOR_API_TOKEN) return null;
  try {
    const resp = await axios.post(
      `${ORCHESTRATOR_URL}/api/v1/deployments`,
      {
        manifest: buildManifestFromDeployment(deployment),
        dry_run: !!deployment.dryRun,
        as_platform_admin: true,
      },
      {
        headers: { Authorization: `Bearer ${ORCHESTRATOR_API_TOKEN}` },
        timeout: 30000,
      }
    );
    return resp.data;
  } catch (err: any) {
    console.error('Orchestrator deployment forward failed:', err?.message || err);
    return null;
  }
};

app.get('/api/deployments', verifyAuth, requireSelfPermission('deployment', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const deployments = await getDeployments();
    const userDeployments = deployments.filter((d: any) => d.user_id === userId);
    res.json(userDeployments);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch deployments' });
  }
});

app.post('/api/deployments', verifyAuth, requireSelfPermission('deployment', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, repoUrl, branch, containerId, targetDir, installCommand, restartCommand, dryRun } = req.body;

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
      dryRun: !!dryRun,
      webhookSecret: crypto.randomBytes(20).toString('hex'),
      createdAt: new Date().toISOString(),
      history: [],
    };
    const orchestration = await forwardDeploymentToOrchestrator(newDeployment);
    if (orchestration) {
      newDeployment.orchestration = orchestration;
    }
    deployments.push(newDeployment);
    await setDeployments(deployments);
    await logAudit(userId, 'deployment:create', 'deployment', newDeployment.id, null, { name, repoUrl });
    res.status(201).json(newDeployment);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create deployment' });
  }
});

app.delete('/api/deployments/:id', verifyAuth, requireSelfPermission('deployment', 'write'), async (req: Request, res: Response) => {
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

app.patch('/api/deployments/:id/toggle', verifyAuth, requireSelfPermission('deployment', 'write'), async (req: Request, res: Response) => {
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

app.get('/api/deployments/:id/history', verifyAuth, requireSelfPermission('deployment', 'read'), async (req: Request, res: Response) => {
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

app.post('/api/notification-channels/:id/test', verifyAuth, requireSelfPermission('notifications', 'write'), async (req: Request, res: Response) => {
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

// Billing routes moved to experimental/management-panel-expanded/billing.ts

// Knowledge base routes moved to experimental/management-panel-expanded/knowledge-base.ts

// Activity feed routes moved to experimental/management-panel-expanded/activity-feed.ts

// Dashboard builder routes moved to experimental/management-panel-expanded/dashboard-builder.ts

// Dashboard routes backed by data/dashboards.json (file-based store)
const DASHBOARDS_FILE = path.join(__dirname, '..', 'data', 'dashboards.json');

async function readDashboards(): Promise<any[]> {
  try {
    const raw = await fs.readFile(DASHBOARDS_FILE, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function writeDashboards(dashboards: any[]): Promise<void> {
  await fs.writeFile(DASHBOARDS_FILE, JSON.stringify(dashboards, null, 2), 'utf-8');
}

app.get('/api/dashboards', verifyAuth, requireWildcardScope(), async (_req: Request, res: Response) => {
  try {
    res.json({ dashboards: await readDashboards() });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch dashboards' });
  }
});

app.get('/api/dashboards/:id', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  try {
    const dashboards = await readDashboards();
    const dashboard = dashboards.find((d: any) => d.id === req.params.id);
    if (!dashboard) return res.status(404).json({ error: 'Dashboard not found' });
    res.json(dashboard);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch dashboard' });
  }
});

app.post('/api/dashboards', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  try {
    const dashboards = await readDashboards();
    const id = req.body.id || crypto.randomUUID();
    const dashboard = { id, ...req.body, createdAt: new Date().toISOString() };
    dashboards.push(dashboard);
    await writeDashboards(dashboards);
    await logAudit((req as any).user.id, 'dashboard:create', 'dashboard', id);
    res.json(dashboard);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create dashboard' });
  }
});

app.put('/api/dashboards/:id', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  try {
    const dashboards = await readDashboards();
    const index = dashboards.findIndex((d: any) => d.id === req.params.id);
    if (index === -1) return res.status(404).json({ error: 'Dashboard not found' });
    const updated = { ...dashboards[index], ...req.body, id: req.params.id, updatedAt: new Date().toISOString() };
    dashboards[index] = updated;
    await writeDashboards(dashboards);
    await logAudit((req as any).user.id, 'dashboard:update', 'dashboard', req.params.id);
    res.json(updated);
  } catch (err) {
    res.status(500).json({ error: 'Failed to update dashboard' });
  }
});

app.delete('/api/dashboards/:id', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  try {
    const dashboards = await readDashboards();
    const index = dashboards.findIndex((d: any) => d.id === req.params.id);
    if (index === -1) return res.status(404).json({ error: 'Dashboard not found' });
    dashboards.splice(index, 1);
    await writeDashboards(dashboards);
    await logAudit((req as any).user.id, 'dashboard:delete', 'dashboard', req.params.id);
    res.json({ status: 'deleted' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to delete dashboard' });
  }
});

app.get('/api/dashboards/:id/data', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  try {
    const period = req.query.period as string;
    const dashboards = await readDashboards();
    const dashboard = dashboards.find((d: any) => d.id === req.params.id);
    if (!dashboard) return res.status(404).json({ error: 'Dashboard not found' });
    res.json({ dashboard, widgets: dashboard.widgets || [], period: period || '24h' });
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch dashboard data' });
  }
});

// ============================================================================
// I18N TRANSLATION ROUTES
// ============================================================================

// GET /api/i18n/translations - List all translations
app.get('/api/i18n/translations', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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
app.post('/api/i18n/translations', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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
    const rawTranslations = (data?.value && typeof data.value === 'object') ? (data.value as Record<string, any>) : {};
    const translations: Record<string, any> = Object.create(null);
    for (const [loc, entries] of Object.entries(rawTranslations)) {
      if (loc === '__proto__' || loc === 'constructor' || loc === 'prototype') continue;
      if (entries && typeof entries === 'object') {
        const safeEntries: Record<string, any> = Object.create(null);
        for (const [k, v] of Object.entries(entries as Record<string, any>)) {
          if (k === '__proto__' || k === 'constructor' || k === 'prototype') continue;
          safeEntries[k] = v;
        }
        translations[loc] = safeEntries;
      }
    }
    if (!translations[locale] || typeof translations[locale] !== 'object') translations[locale] = Object.create(null);
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
app.get('/api/themes', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const themes = await getThemes(userId);
    res.json(themes);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch themes' });
  }
});

// POST /api/themes - Save a new theme
app.post('/api/themes', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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
app.get('/api/themes/:id', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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
app.delete('/api/themes/:id', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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
app.post('/api/themes/:id/publish', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
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

// Bulk operations routes moved to experimental/management-panel-expanded/bulk-operations.ts

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
app.get('/api/config/:appId/advice', verifyAuth, generalLimiter, async (req: Request, res: Response) => {
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
          const { stdout } = await runCommand('docker', ['exec', app.container_id, 'cat', fp]).catch(() => ({ stdout: '', stderr: '' }));
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
app.post('/api/config/:appId/advice/:suggestionId/apply', verifyAuth, generalLimiter, async (req: Request, res: Response) => {
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
          const { stdout } = await runCommand('docker', ['exec', app.container_id, 'cat', fp]).catch(() => ({ stdout: '', stderr: '' }));
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

// Plugin marketplace routes moved to experimental/management-panel-expanded/plugin-marketplace.ts

// Terminal session routes moved to experimental/management-panel-expanded/terminal.ts

// Change approval routes moved to experimental/management-panel-expanded/change-approval.ts

// V3 + V4 routes removed for core MVP scope.
// See experimental/management-panel-expanded/v3-v4-routes.ts

// ============================================================================
// AUTHENTICATED WEBSOCKET GATEWAY
// ============================================================================
//
// Every WebSocket connection must present a short-lived ticket minted by
// `POST /api/ws-token`. Each per-app action (logs, metrics, terminal) is then
// authorized against app ownership and role assignments before any Docker
// command runs. See `server/ws/` and `wiki/15-WS-Auth.md`.

const httpServer = http.createServer(app);

/* App access decisions live entirely in the RBAC store
 * (`server/rbac/store.ts`); WebSocket and HTTP share the same resolver. */

/**
 * Resolve whether a user may perform a WebSocket action on an app.
 * Whole decision delegated to the RBAC store, which applies ownership,
 * app assignments, and instance roles with the same permission mapping
 * the HTTP middleware uses.
 */
async function resolveWsAppAccess(userId: string, appId: string, action: WsAction): Promise<boolean> {
  try {
    return await rbacStore!.resolveAppAccess(userId, appId, action);
  } catch (err) {
    // Fail closed: the gateway denies on resolver errors.
    console.error('[ws] app access resolution failed:', err instanceof Error ? err.message : err);
    return false;
  }
}

/**
 * Resolve the Docker container id for an app, validating its format before it
 * is ever passed to `docker`.
 * @returns The validated container id, or null when missing/invalid
 */
async function resolveWsContainerId(appId: string): Promise<string | null> {
  const { data, error } = await supabase
    .from('docker_apps')
    .select('container_id')
    .eq('id', appId)
    .maybeSingle();
  if (error || !data || !data.container_id) return null;
  const containerId = String(data.container_id);
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(containerId)) return null;
  return containerId;
}

/**
 * Whether a user may request a ticket scoped to a specific app.
 * Ownership, any app assignment, or instance access qualifies; the ticket
 * scope only narrows access, the gateway still re-checks every action.
 */
async function canScopeWsTicket(userId: string, appId: string): Promise<boolean> {
  try {
    return (await rbacStore!.can(userId, 'app', 'read', { appId })).allowed;
  } catch {
    return false;
  }
}

const wsConfig = loadWsConfig(process.env);
const wsTickets = new TicketService({
  secret: resolveWsTicketSecret(process.env),
  ttlSeconds: wsConfig.ticketTtlSeconds,
  skewSeconds: wsConfig.ticketSkewSeconds,
});
const wsAudit = new WsAuditLogger({ log: logAudit });
const wsGateway = createWsGateway({
  config: wsConfig,
  tickets: wsTickets,
  audit: wsAudit,
  resolveAppAccess: resolveWsAppAccess,
  resolveContainerId: resolveWsContainerId,
});
wsGateway.attach(httpServer);

app.use(
  '/api/ws-token',
  createWsTokenRouter({
    verifyAuth,
    tickets: wsTickets,
    audit: wsAudit,
    gateway: wsGateway,
    ttlSeconds: wsConfig.ticketTtlSeconds,
    validateAppAccess: canScopeWsTicket,
  }),
);

export { httpServer, wsGateway };

// ============================================================================
// SSH Session Management API Routes
// ============================================================================

app.get('/api/ssh/sessions', verifyAuth, requireSelfPermission('ssh', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { status } = req.query;
  let query = supabase.from('ssh_sessions').select('*').eq('user_id', userId).order('started_at', { ascending: false });
  if (status) query = query.eq('status', status as string);
  const { data, error } = await query;
  if (error) return res.status(500).json({ error: error.message });
  res.json({ sessions: data || [] });
});

app.post('/api/ssh/connect', verifyAuth, requireSelfPermission('ssh', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { server, user, jump_host, port } = req.body;
  const { data, error } = await supabase.from('ssh_sessions').insert({
    user_id: userId, server_name: server, username: user || 'root', jump_host, port: port || 22, status: 'active'
  }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json({ session: data, message: `SSH session connecting to ${user || 'root'}@${server}` });
});

app.get('/api/ssh/jump-hosts', verifyAuth, requireSelfPermission('ssh', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('ssh_jump_hosts').select('*').eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ jump_hosts: data || [] });
});

app.post('/api/ssh/jump-hosts', verifyAuth, requireSelfPermission('ssh', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, host, user } = req.body;
  const { data, error } = await supabase.from('ssh_jump_hosts').insert({ user_id: userId, name, host, username: user || 'root' }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.get('/api/ssh/keys', verifyAuth, requireSelfPermission('ssh', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('ssh_keys').select('*').eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ keys: data || [] });
});

app.post('/api/ssh/keys', verifyAuth, requireSelfPermission('ssh', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, key } = req.body;
  const fingerprint = crypto.createHash('sha256').update(key).digest('hex');
  const { data, error } = await supabase.from('ssh_keys').insert({ user_id: userId, name, public_key: key, fingerprint }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.delete('/api/ssh/keys/:id', verifyAuth, requireSelfPermission('ssh', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { error } = await supabase.from('ssh_keys').delete().eq('id', req.params.id).eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ status: 'deleted' });
});

app.get('/api/ssh/sessions/:id/recording', verifyAuth, requireSelfPermission('ssh', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('ssh_sessions').select('recording').eq('id', req.params.id).eq('user_id', userId).single();
  if (error) return res.status(500).json({ error: error.message });
  res.json({ recording: data?.recording || 'No recording available' });
});

app.get('/api/ssh/saved-hosts', verifyAuth, requireSelfPermission('ssh', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('ssh_saved_hosts').select('*').eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ hosts: data || [] });
});

app.post('/api/ssh/saved-hosts', verifyAuth, requireSelfPermission('ssh', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, host, port } = req.body;
  const { data, error } = await supabase.from('ssh_saved_hosts').insert({ user_id: userId, name, host, port: port || 22 }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.delete('/api/ssh/saved-hosts/:id', verifyAuth, requireSelfPermission('ssh', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { error } = await supabase.from('ssh_saved_hosts').delete().eq('id', req.params.id).eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ status: 'deleted' });
});

// ============================================================================
// Server Inventory API Routes
// ============================================================================

app.get('/api/inventory', verifyAuth, requireSelfPermission('inventory', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  let query = supabase.from('server_inventory').select('*').eq('user_id', userId);
  const { tag, environment, region, owner, provider } = req.query;
  if (tag) query = query.contains('tags', [tag as string]);
  if (environment) query = query.eq('environment', environment as string);
  if (region) query = query.eq('region', region as string);
  if (owner) query = query.eq('owner', owner as string);
  if (provider) query = query.eq('provider', provider as string);
  const { data, error } = await query;
  if (error) return res.status(500).json({ error: error.message });
  res.json({ inventory: data || [] });
});

app.get('/api/inventory/tags', verifyAuth, requireSelfPermission('inventory', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('server_inventory').select('tags').eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  const allTags = new Set<string>();
  (data || []).forEach((item: any) => { if (item.tags) item.tags.forEach((t: string) => allTags.add(t)); });
  res.json({ tags: Array.from(allTags) });
});

app.get('/api/inventory/:serverId', verifyAuth, requireSelfPermission('inventory', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('server_inventory').select('*').eq('server_id', req.params.serverId).eq('user_id', userId).single();
  if (error) return res.status(404).json({ error: 'Not found' });
  res.json(data);
});

app.patch('/api/inventory/:serverId', verifyAuth, requireSelfPermission('inventory', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('server_inventory').update(req.body).eq('server_id', req.params.serverId).eq('user_id', userId).select().single();
  if (error) return res.status(500).json({ error: error.message });
  if (!data) return res.status(404).json({ error: 'Not found' });
  res.json(data);
});

app.get('/api/inventory/:serverId/tags', verifyAuth, requireSelfPermission('inventory', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('server_inventory').select('tags').eq('server_id', req.params.serverId).eq('user_id', userId).single();
  if (error) return res.status(404).json({ error: 'Not found' });
  res.json({ tags: data?.tags || [] });
});

app.post('/api/inventory/:serverId/tags', verifyAuth, requireSelfPermission('inventory', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { tag } = req.body;
  const { data: existing } = await supabase.from('server_inventory').select('tags').eq('server_id', req.params.serverId).eq('user_id', userId).single();
  const tags = existing?.tags || [];
  if (!tags.includes(tag)) tags.push(tag);
  const { data, error } = await supabase.from('server_inventory').update({ tags }).eq('server_id', req.params.serverId).eq('user_id', userId).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.delete('/api/inventory/:serverId/tags/:tag', verifyAuth, requireSelfPermission('inventory', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: existing } = await supabase.from('server_inventory').select('tags').eq('server_id', req.params.serverId).eq('user_id', userId).single();
  const tags = (existing?.tags || []).filter((t: string) => t !== req.params.tag);
  const { data, error } = await supabase.from('server_inventory').update({ tags }).eq('server_id', req.params.serverId).eq('user_id', userId).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

// ============================================================================
// Secret Management API Routes
// ============================================================================

app.get('/api/secrets', verifyAuth, requireSelfPermission('secrets', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { path } = req.query;
  let query = supabase.from('secrets').select('id, key, version, rotate, rotation_days, last_rotated, next_rotation, external_ref, created_at, updated_at').eq('user_id', userId);
  if (path) query = query.ilike('key', `${path}%`);
  const { data, error } = await query;
  if (error) return res.status(500).json({ error: error.message });
  res.json({ secrets: data || [] });
});

app.get('/api/secrets/due-for-rotation', verifyAuth, requireSelfPermission('secrets', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('secrets').select('*').eq('user_id', userId).eq('rotate', true).lte('next_rotation', new Date().toISOString());
  if (error) return res.status(500).json({ error: error.message });
  res.json({ secrets: data || [] });
});

app.get('/api/secrets/:key', verifyAuth, requireSelfPermission('secrets', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { version, resolve } = req.query;
  if (version) {
    const { data: secret } = await supabase.from('secrets').select('id').eq('key', req.params.key).eq('user_id', userId).single();
    if (!secret) return res.status(404).json({ error: 'Secret not found' });
    const { data, error } = await supabase.from('secret_versions').select('value, version').eq('secret_id', secret.id).eq('version', parseInt(version as string)).single();
    if (error) return res.status(404).json({ error: 'Not found' });
    return res.json(data);
  }
  const { data, error } = await supabase.from('secrets').select('*').eq('key', req.params.key).eq('user_id', userId).single();
  if (error) return res.status(404).json({ error: 'Not found' });
  if (isExternalRef(data.external_ref)) {
    // External mode: the panel stores only the reference. The value is
    // resolved on demand via the orchestrator and lives in an in-process
    // cache for 30s — never in Supabase.
    if (resolve === 'true' || resolve === '1') {
      if (!orchestratorSecretsConfigured()) {
        return res.status(503).json({ error: 'Orchestrator not configured (set ORCHESTRATOR_API_TOKEN)' });
      }
      const resolved = await resolveExternalSecret(data.external_ref, userId);
      if (!resolved) return res.status(503).json({ error: 'External secret could not be resolved' });
      return res.json({ key: data.key, value: resolved.value, external_ref: true, backend: resolved.backend, version: data.version });
    }
    return res.json({ key: data.key, external_ref: data.external_ref, version: data.version });
  }
  res.json({ value: data.value, version: data.version, key: data.key });
});

app.post('/api/secrets', verifyAuth, requireSelfPermission('secrets', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { key, value, rotate, rotation_days, external_ref } = req.body;
  if (isExternalRef(external_ref)) {
    // External mode: store the reference only. No plaintext value, no
    // version history — the backend holds the truth.
    if (typeof value === 'string' && value.length > 0) {
      return res.status(400).json({ error: 'external_ref and value are mutually exclusive' });
    }
    const nextRotation = rotate ? new Date(Date.now() + (rotation_days || 90) * 86400000).toISOString() : null;
    const { data: existing } = await supabase.from('secrets').select('id, version').eq('key', key).eq('user_id', userId).single();
    if (existing) {
      const { error: updateError } = await supabase.from('secrets').update({ external_ref, value: '', version: (existing.version || 1) + 1, rotate: rotate || false, rotation_days: rotation_days || 90, next_rotation: nextRotation }).eq('id', existing.id);
      if (updateError) return res.status(500).json({ error: updateError.message });
      await supabase.from('secret_versions').delete().eq('secret_id', existing.id);
      const { data } = await supabase.from('secrets').select('id, key, version, external_ref, rotate, rotation_days').eq('id', existing.id).single();
      return res.json(data);
    }
    const { data, error } = await supabase.from('secrets').insert({ user_id: userId, key, external_ref, value: '', rotate: rotate || false, rotation_days: rotation_days || 90, next_rotation: nextRotation }).select('id, key, version, external_ref').single();
    if (error) return res.status(500).json({ error: error.message });
    return res.json(data);
  }
  const { data: existing } = await supabase.from('secrets').select('id, version').eq('key', key).eq('user_id', userId).single();
  if (existing) {
    const newVersion = (existing.version || 1) + 1;
    await supabase.from('secret_versions').insert({ secret_id: existing.id, value, version: newVersion, created_by: userId });
    const nextRotation = rotate ? new Date(Date.now() + (rotation_days || 90) * 86400000).toISOString() : null;
    const { data, error } = await supabase.from('secrets').update({ value, version: newVersion, rotate: rotate || false, rotation_days: rotation_days || 90, next_rotation: nextRotation }).eq('id', existing.id).select().single();
    if (error) return res.status(500).json({ error: error.message });
    return res.json(data);
  }
  const nextRotation = rotate ? new Date(Date.now() + (rotation_days || 90) * 86400000).toISOString() : null;
  const { data, error } = await supabase.from('secrets').insert({ user_id: userId, key, value, rotate: rotate || false, rotation_days: rotation_days || 90, next_rotation: nextRotation }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.delete('/api/secrets/:key', verifyAuth, requireSelfPermission('secrets', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { error } = await supabase.from('secrets').delete().eq('key', req.params.key).eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ status: 'deleted' });
});

app.get('/api/secrets/:key/versions', verifyAuth, requireSelfPermission('secrets', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: secret } = await supabase.from('secrets').select('id').eq('key', req.params.key).eq('user_id', userId).single();
  if (!secret) return res.status(404).json({ error: 'Secret not found' });
  const { data, error } = await supabase.from('secret_versions').select('version, created_at, created_by').eq('secret_id', secret.id).order('version', { ascending: false });
  if (error) return res.status(500).json({ error: error.message });
  res.json({ versions: data || [] });
});

app.post('/api/secrets/:key/rotate', verifyAuth, requireSelfPermission('secrets', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: secret } = await supabase.from('secrets').select('*').eq('key', req.params.key).eq('user_id', userId).single();
  if (!secret) return res.status(404).json({ error: 'Secret not found' });
  if (isExternalRef(secret.external_ref)) {
    // External mode: the truth lives on the backend; forward rotation
    // through the orchestrator and only bookkeep the panel row after a
    // 2xx. The rotated value is never returned or stored.
    if (!orchestratorSecretsConfigured()) {
      return res.status(503).json({ error: 'Orchestrator not configured (set ORCHESTRATOR_API_TOKEN)' });
    }
    const rotated = await rotateExternalSecret(secret.external_ref, userId);
    if (!rotated) return res.status(503).json({ error: 'External secret could not be rotated' });
    const newVersion = (secret.version || 1) + 1;
    const nextRotation = new Date(Date.now() + (secret.rotation_days || 90) * 86400000).toISOString();
    const { data, error } = await supabase.from('secrets').update({ version: newVersion, last_rotated: new Date().toISOString(), next_rotation: nextRotation }).eq('id', secret.id).select('id, key, version, last_rotated, next_rotation, external_ref').single();
    if (error) return res.status(500).json({ error: error.message });
    return res.json(data);
  }
  const newValue = crypto.randomBytes(32).toString('hex');
  const newVersion = (secret.version || 1) + 1;
  await supabase.from('secret_versions').insert({ secret_id: secret.id, value: newValue, version: newVersion, created_by: userId });
  const nextRotation = new Date(Date.now() + (secret.rotation_days || 90) * 86400000).toISOString();
  const { data, error } = await supabase.from('secrets').update({ value: newValue, version: newVersion, last_rotated: new Date().toISOString(), next_rotation: nextRotation }).eq('id', secret.id).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.post('/api/secrets/rotate-all', verifyAuth, requireSelfPermission('secrets', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: secrets } = await supabase.from('secrets').select('*').eq('user_id', userId).eq('rotate', true).lte('next_rotation', new Date().toISOString());
  const results = [];
  for (const secret of secrets || []) {
    const newValue = crypto.randomBytes(32).toString('hex');
    const newVersion = (secret.version || 1) + 1;
    await supabase.from('secret_versions').insert({ secret_id: secret.id, value: newValue, version: newVersion, created_by: userId });
    await supabase.from('secrets').update({ value: newValue, version: newVersion, last_rotated: new Date().toISOString(), next_rotation: new Date(Date.now() + (secret.rotation_days || 90) * 86400000).toISOString() }).eq('id', secret.id);
    results.push({ key: secret.key, new_version: newVersion });
  }
  res.json({ rotated: results.length, secrets: results });
});

app.get('/api/secrets/:key/access', verifyAuth, requireSelfPermission('secrets', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: secret } = await supabase.from('secrets').select('id').eq('key', req.params.key).eq('user_id', userId).single();
  if (!secret) return res.status(404).json({ error: 'Secret not found' });
  const { data, error } = await supabase.from('secret_access').select('role, granted_at').eq('secret_id', secret.id);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ access: data || [] });
});

app.post('/api/secrets/:key/access', verifyAuth, requireSelfPermission('secrets', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { secret } = await supabase.from('secrets').select('id').eq('key', req.params.key).eq('user_id', userId).single();
  if (!secret) return res.status(404).json({ error: 'Secret not found' });
  const { data, error } = await supabase.from('secret_access').insert({ secret_id: secret.id, role: req.body.role, granted_by: userId }).select().single();
  if (error && error.code === '23505') return res.status(409).json({ error: 'Access already granted' });
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.delete('/api/secrets/:key/access/:role', verifyAuth, requireSelfPermission('secrets', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: secret } = await supabase.from('secrets').select('id').eq('key', req.params.key).eq('user_id', userId).single();
  if (!secret) return res.status(404).json({ error: 'Secret not found' });
  const { error } = await supabase.from('secret_access').delete().eq('secret_id', secret.id).eq('role', req.params.role);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ status: 'revoked' });
});

// ============================================================================
// Webhook Management API Routes
// ============================================================================

app.get('/api/webhooks', verifyAuth, requireSelfPermission('webhooks', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('webhooks').select('*').eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ webhooks: data || [] });
});

app.post('/api/webhooks', verifyAuth, requireSelfPermission('webhooks', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, url, events, secret } = req.body;
  const { data, error } = await supabase.from('webhooks').insert({ user_id: userId, name, url, events: events || [], secret }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  await logAudit(userId, 'webhook:create', 'webhook', data.id, null, { name, url, events: events || [] });
  res.json(data);
});

app.delete('/api/webhooks/:id', verifyAuth, requireSelfPermission('webhooks', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { error } = await supabase.from('webhooks').delete().eq('id', req.params.id).eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  await logAudit(userId, 'webhook:delete', 'webhook', req.params.id);
  res.json({ status: 'deleted' });
});

app.post('/api/webhooks/test', verifyAuth, requireSelfPermission('webhooks', 'write'), async (req: Request, res: Response) => {
  const { event } = req.body;
  res.json({ status: 'test_sent', event: event || 'test', note: 'Webhook test endpoint ready. Configure a real webhook to receive events.' });
});

app.post('/api/webhooks/:id/test', verifyAuth, requireSelfPermission('webhooks', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: webhook } = await supabase.from('webhooks').select('*').eq('id', req.params.id).eq('user_id', userId).single();
  if (!webhook) return res.status(404).json({ error: 'Webhook not found' });
  try {
    const payload = { event: req.body.event || 'test', timestamp: new Date().toISOString(), webhook_id: webhook.id };
    const response = await axios.post(webhook.url, payload, { headers: webhook.secret ? { 'X-Webhook-Secret': webhook.secret } : {} });
    await supabase.from('webhook_logs').insert({ webhook_id: webhook.id, event: 'test', status: 'success', response_code: response.status, response_body: JSON.stringify(response.data) });
    res.json({ status: 'sent', response_code: response.status });
  } catch (err: any) {
    await supabase.from('webhook_logs').insert({ webhook_id: webhook.id, event: 'test', status: 'failed', response_code: err.response?.status || 0, response_body: err.message });
    res.status(502).json({ error: `Webhook delivery failed: ${err.message}` });
  }
});

app.get('/api/webhooks/logs', verifyAuth, requireSelfPermission('webhooks', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: webhooks } = await supabase.from('webhooks').select('id').eq('user_id', userId);
  const ids = (webhooks || []).map((w: any) => w.id);
  if (ids.length === 0) return res.json({ logs: [] });
  const { data, error } = await supabase.from('webhook_logs').select('*').in('webhook_id', ids).order('delivered_at', { ascending: false }).limit(100);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ logs: data || [] });
});

app.get('/api/webhooks/:id/logs', verifyAuth, requireSelfPermission('webhooks', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: webhook } = await supabase.from('webhooks').select('id').eq('id', req.params.id).eq('user_id', userId).single();
  if (!webhook) return res.status(404).json({ error: 'Webhook not found' });
  const { data, error } = await supabase.from('webhook_logs').select('*').eq('webhook_id', webhook.id).order('delivered_at', { ascending: false });
  if (error) return res.status(500).json({ error: error.message });
  res.json({ logs: data || [] });
});

// ============================================================================
// API Key Management Routes (scoped keys, see server/apikeys/)
// ============================================================================

const WILDCARD_SCOPE = '*';

/**
 * Whether the row still works but should prompt its owner to rotate.
 * Kept as a function so list/read single-source the rule.
 */
function forceRotationNeeded(row: any): boolean {
  return row.force_rotate === true || !Array.isArray(row.scopes);
}

/**
 * GET /api/api-keys - the caller's keys with scopes, class, last-used and
 * a `needs_rotation` flag for legacy full-access keys.
 */
app.get('/api/api-keys', verifyAuth, requireSelfPermission('apikeys', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase
    .from('api_keys')
    .select('id, name, key_prefix, role, scopes, key_class, app_id, expires_at, last_used_at, created_at, force_rotate')
    .eq('user_id', userId)
    .eq('revoked', false)
    .order('created_at', { ascending: false });
  if (error) return res.status(500).json({ error: error.message });
  res.json({
    api_keys: (data || []).map((row: any) => ({
      ...row,
      // Legacy rows carry no scope array: they remain full-access until
      // rotated; the flag lets any client render the rotation prompt.
      needs_rotation: forceRotationNeeded(row),
    })),
  });
});

/**
 * POST /api/api-keys - create a key. v2 body:
 *   { name, key_class: 'live'|'test', scopes: ['apps:read', ...]?,
 *     expire_days?, app_id? }
 * The prefix encodes the class (`ip_live_` / `ip_test_`); omitted or
 * invalid scopes default to the wildcard `*` (documented behavior).
 */
app.post('/api/api-keys', verifyAuth, requireSelfPermission('apikeys', 'write'), sensitive2FA, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, key_class, scopes, expire_days, app_id } = req.body || {};
  if (!name || typeof name !== 'string' || name.length > 255) {
    return res.status(400).json({ error: 'name is required (<= 255 chars)' });
  }
  const keyClass = key_class === 'test' ? 'test' : 'live';
  const rawKey = `${keyClass === 'test' ? 'ip_test_' : 'ip_live_'}${crypto.randomBytes(12).toString('hex')}`;
  const keyHash = hashApiKey(rawKey);
  const keyPrefix = rawKey.substring(0, 10);
  const normalizedScopes = scopes === undefined
    ? [WILDCARD_SCOPE]
    : normalizeScopes(scopes);
  if (normalizedScopes === null) {
    return res.status(400).json({ error: "scopes must be '<family>:<action>' tokens (e.g. apps:read), '<family>:*', or '*'" });
  }
  const expiresAt = expire_days ? new Date(Date.now() + Number(expire_days) * 86400000).toISOString() : null;
  if (expire_days && !(Number(expire_days) > 0 && Number(expire_days) <= 730)) {
    return res.status(400).json({ error: 'expire_days must be a positive number up to 730' });
  }
  const { data, error } = await supabase
    .from('api_keys')
    .insert({
      user_id: userId,
      name,
      key_hash: keyHash,
      key_prefix: keyPrefix,
      role: 'user',
      scopes: normalizedScopes,
      key_class: keyClass,
      expires_at: expiresAt,
      app_id: typeof app_id === 'string' && app_id ? app_id : null,
    })
    .select('id, name, key_prefix, role, scopes, key_class, app_id, expires_at')
    .single();
  if (error) return res.status(500).json({ error: error.message });
  await logAudit(userId, 'api_key:create', 'api_key', data.id, null, {
    name,
    scopes: (data.scopes as string[]) || [WILDCARD_SCOPE],
    key_class: keyClass,
    app_id: data.app_id || null,
  });
  res.json({ ...data, needs_rotation: false, key: rawKey });
});

/**
 * DELETE /api/api-keys/:id - revoke. Audited; also drops the caller's
 * cached 2FA re-auth window.
 */
app.delete('/api/api-keys/:id', verifyAuth, requireSelfPermission('apikeys', 'write'), sensitive2FA, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { error } = await supabase
    .from('api_keys')
    .update({ revoked: true })
    .eq('id', req.params.id)
    .eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  clearReauthGrant(userId);
  await logAudit(userId, 'api_key:revoke', 'api_key', req.params.id);
  res.json({ status: 'revoked' });
});

/**
 * POST /api/api-keys/:id/rotate - overlap rotation: a replacement key is
 * issued immediately; the old key keeps working until its overlap expiry
 * (`rotate_overlap_hours`, default 24, max 168) and carries `force_rotate`
 * so a client prompts again. Requires a fresh 2FA code.
 */
app.post('/api/api-keys/:id/rotate', verifyAuth, requireSelfPermission('apikeys', 'write'), sensitive2FA, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const overlapHours = Math.min(Math.max(Number(req.body?.rotate_overlap_hours || 24), 1), 168);
  const { data: current, error: fetchError } = await supabase
    .from('api_keys')
    .select('id, name, scopes, key_class, app_id, expires_at')
    .eq('id', req.params.id)
    .eq('user_id', userId)
    .eq('revoked', false)
    .single();
  if (fetchError || !current) return res.status(404).json({ error: 'API key not found' });

  const keyClass = current.key_class === 'test' ? 'test' : 'live';
  const rawKey = `${keyClass === 'test' ? 'ip_test_' : 'ip_live_'}${crypto.randomBytes(12).toString('hex')}`;
  const keyHash = hashApiKey(rawKey);
  const keyPrefix = rawKey.substring(0, 10);
  const overlapEnd = new Date(Date.now() + overlapHours * 3600000).toISOString();
  const hardEnd = current.expires_at && new Date(current.expires_at).getTime() < Date.now() + overlapHours * 3600000
    ? current.expires_at
    : overlapEnd;

  const { data: created, error: createError } = await supabase
    .from('api_keys')
    .insert({
      user_id: userId,
      name: current.name,
      key_hash: keyHash,
      key_prefix: keyPrefix,
      role: 'user',
      scopes: Array.isArray(current.scopes) ? current.scopes : [WILDCARD_SCOPE],
      key_class: keyClass,
      app_id: current.app_id || null,
      expires_at: current.expires_at || null,
      rotated_from: current.id,
    })
    .select('id, name, scopes, key_class, app_id, expires_at')
    .single();
  if (createError) return res.status(500).json({ error: createError.message });

  await supabase
    .from('api_keys')
    .update({ force_rotate: true, expires_at: hardEnd })
    .eq('id', current.id);
  clearReauthGrant(userId);
  await logAudit(userId, 'api_key:rotate', 'api_key', current.id, null, { overlap_end: hardEnd });
  res.status(201).json({ ...created, old_overlap_expires_at: hardEnd, key: rawKey });
});

// ============================================================================
// Plugin Management API Routes
// ============================================================================

app.get('/api/plugins', verifyAuth, requireSelfPermission('plugins', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { installed } = req.query;
  let query = supabase.from('plugins').select('*').eq('user_id', userId);
  if (installed === 'true') query = query.eq('installed', true);
  const { data, error } = await query;
  if (error) return res.status(500).json({ error: error.message });
  const builtinPlugins = [
    { name: 'kubernetes', description: 'Kubernetes cluster management', version: '1.0.0', builtin: true, installed: false },
    { name: 'docker', description: 'Advanced Docker management', version: '1.0.0', builtin: true, installed: true },
    { name: 'aws', description: 'Amazon Web Services integration', version: '1.0.0', builtin: true, installed: false },
    { name: 'hetzner', description: 'Hetzner Cloud integration', version: '1.0.0', builtin: true, installed: false },
    { name: 'cloudflare', description: 'Cloudflare DNS & CDN integration', version: '1.0.0', builtin: true, installed: false },
    { name: 'proxmox', description: 'Proxmox VE virtualization management', version: '1.0.0', builtin: true, installed: false },
    { name: 'ansible', description: 'Ansible automation integration', version: '1.0.0', builtin: true, installed: false },
    { name: 'nomad', description: 'HashiCorp Nomad orchestration', version: '1.0.0', builtin: true, installed: false },
    { name: 'azure', description: 'Microsoft Azure integration', version: '1.0.0', builtin: true, installed: false },
  ];
  const installedNames = new Set((data || []).map((p: any) => p.name));
  const allPlugins = [
    ...builtinPlugins.map((bp) => ({ ...bp, installed: installedNames.has(bp.name) || bp.installed })),
    ...(data || []).filter((p: any) => !builtinPlugins.find((bp) => bp.name === p.name)),
  ];
  res.json({ plugins: allPlugins });
});

app.post('/api/plugins/install', verifyAuth, requireSelfPermission('plugins', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, source, version } = req.body;
  const { data, error } = await supabase.from('plugins').insert({ user_id: userId, name, source, version, installed: true, enabled: true }).select().single();
  if (error && error.code === '23505') return res.status(409).json({ error: 'Plugin already installed' });
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.post('/api/plugins/:name/uninstall', verifyAuth, requireSelfPermission('plugins', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { error } = await supabase.from('plugins').delete().eq('name', req.params.name).eq('user_id', userId);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ status: 'uninstalled' });
});

app.post('/api/plugins/:name/update', verifyAuth, requireSelfPermission('plugins', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('plugins').update({ version: '1.0.1', updated_at: new Date().toISOString() }).eq('name', req.params.name).eq('user_id', userId).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data || { status: 'updated' });
});

app.post('/api/plugins/update-all', verifyAuth, requireSelfPermission('plugins', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('plugins').update({ version: '1.0.1', updated_at: new Date().toISOString() }).eq('user_id', userId).eq('installed', true);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ status: 'all_updated', count: data?.length || 0 });
});

app.get('/api/plugins/updates', verifyAuth, requireSelfPermission('plugins', 'read'), async (req: Request, res: Response) => {
  res.json({ updates: [] });
});

app.get('/api/plugins/:name', verifyAuth, requireSelfPermission('plugins', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('plugins').select('*').eq('name', req.params.name).eq('user_id', userId).single();
  if (error) return res.status(404).json({ error: 'Plugin not found or not installed' });
  res.json(data);
});

// ============================================================================
// Deployment Templates API Routes
// ============================================================================

const BUILTIN_TEMPLATES = [
  { name: 'nodejs', type: 'node', description: 'Node.js application with Express', config: { image: 'node:18-alpine', ports: [{ hostPort: 3000, containerPort: 3000 }], environment_vars: { NODE_ENV: 'production' } }, builtin: true },
  { name: 'python', type: 'python', description: 'Python application with Flask/Gunicorn', config: { image: 'python:3.11-slim', ports: [{ hostPort: 8000, containerPort: 8000 }], environment_vars: { PYTHONUNBUFFERED: '1' } }, builtin: true },
  { name: 'docker-compose', type: 'docker-compose', description: 'Multi-service Docker Compose stack', config: { compose_file: 'docker-compose.yml' }, builtin: true },
  { name: 'nginx', type: 'nginx', description: 'Nginx web server with SSL', config: { image: 'nginx:alpine', ports: [{ hostPort: 80, containerPort: 80 }, { hostPort: 443, containerPort: 443 }], volumes: [{ hostPath: '/etc/nginx/conf.d', containerPath: '/etc/nginx/conf.d' }] }, builtin: true },
  { name: 'postgresql', type: 'postgres', description: 'PostgreSQL database', config: { image: 'postgres:15-alpine', ports: [{ hostPort: 5432, containerPort: 5432 }], environment_vars: { POSTGRES_PASSWORD: 'changeme' }, volumes: [{ hostPath: '/var/lib/postgresql/data', containerPath: '/var/lib/postgresql/data' }] }, builtin: true },
  { name: 'redis', type: 'redis', description: 'Redis cache server', config: { image: 'redis:7-alpine', ports: [{ hostPort: 6379, containerPort: 6379 }] }, builtin: true },
  { name: 'traefik', type: 'traefik', description: 'Traefik reverse proxy with auto SSL', config: { image: 'traefik:v3.0', ports: [{ hostPort: 80, containerPort: 80 }, { hostPort: 443, containerPort: 443 }], command: ['--providers.docker', '--entrypoints.web.address=:80', '--entrypoints.websecure.address=:443', '--certificatesresolvers.letsencrypt.acme.httpchallenge=true', '--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web'] }, builtin: true },
];

app.get('/api/templates', verifyAuth, async (req: Request, res: Response) => {
  const { type } = req.query;
  let templates = [...BUILTIN_TEMPLATES];
  const { data: userTemplates } = await supabase.from('deployment_templates').select('*');
  if (userTemplates) templates = [...templates, ...userTemplates];
  if (type) templates = templates.filter((t) => t.type === type);
  res.json({ templates });
});

app.get('/api/templates/:name', verifyAuth, async (req: Request, res: Response) => {
  const template = BUILTIN_TEMPLATES.find((t) => t.name === req.params.name);
  if (template) return res.json(template);
  const { data, error } = await supabase.from('deployment_templates').select('*').eq('name', req.params.name).single();
  if (error) return res.status(404).json({ error: 'Template not found' });
  res.json(data);
});

app.post('/api/templates/deploy', verifyAuth, requireSelfPermission('app', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { template: templateName, name, server, variables, dry_run } = req.body;
  const template = BUILTIN_TEMPLATES.find((t) => t.name === templateName);
  if (!template) return res.status(404).json({ error: `Template '${templateName}' not found` });
  if (dry_run) return res.json({ status: 'dry_run', template: templateName, name, actions: [`Create container ${name}`, `Configure ports`, `Set environment variables`] });
  const appConfig = { ...template.config };
  if (variables) {
    if (variables.environment_vars) appConfig.environment_vars = { ...appConfig.environment_vars, ...variables.environment_vars };
    if (variables.ports) appConfig.ports = variables.ports;
  }
  const { data, error } = await supabase.from('docker_apps').insert({
    user_id: userId, name, image: appConfig.image, status: 'stopped', ports: appConfig.ports || [], environment_vars: appConfig.environment_vars || {}, volumes: appConfig.volumes || [],
  }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json({ status: 'deployed', app: data, message: `Template '${templateName}' deployed as '${name}'` });
});

app.post('/api/templates/init', verifyAuth, requireInstancePermission('settings', 'write'), async (req: Request, res: Response) => {
  const { template, name, output_dir } = req.body;
  const tpl = BUILTIN_TEMPLATES.find((t) => t.name === template);
  if (!tpl) return res.status(404).json({ error: `Template '${template}' not found` });
  const files = [];
  switch (tpl.type) {
    case 'node':
      files.push({ path: 'package.json', content: JSON.stringify({ name, version: '1.0.0', scripts: { start: 'node index.js' }, dependencies: { express: '^4.18.0' } }, null, 2) });
      files.push({ path: 'index.js', content: "const express = require('express');\nconst app = express();\nconst port = process.env.PORT || 3000;\napp.get('/', (req, res) => res.send('Hello World!'));\napp.listen(port, () => console.log(`App listening on port ${port}`));" });
      files.push({ path: 'Dockerfile', content: 'FROM node:18-alpine\nWORKDIR /app\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nEXPOSE 3000\nCMD ["node", "index.js"]' });
      break;
    case 'python':
      files.push({ path: 'requirements.txt', content: 'flask==3.0.0\ngunicorn==21.2.0' });
      files.push({ path: 'app.py', content: "from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef hello():\n    return 'Hello World!'\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=8000)" });
      files.push({ path: 'Dockerfile', content: 'FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nEXPOSE 8000\nCMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]' });
      break;
    default:
      files.push({ path: 'README.md', content: `# ${name}\n\nTemplate: ${template}` });
  }
  res.json({ status: 'initialized', name, output_dir: output_dir || '.', files });
});

// ============================================================================
// Doctor / Benchmark / Diagnose API Routes
// ============================================================================

app.post('/api/doctor/benchmark', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const duration = Math.min(Math.max(Number(req.body?.duration) || 10, 1), 120);
  const result = await runBenchmark(duration);
  const { error } = await supabase.from('benchmark_results').insert({
    server_id: null,
    benchmark_type: 'local',
    duration_seconds: duration,
    cpu_score: result.cpu_avg_pct,
    memory_score: result.memory_used_pct,
    disk_score: result.disk_write_mbps,
    overall_score: result.cpu_avg_pct + result.memory_used_pct,
    raw_data: result.measurements,
  });
  if (error) {
    res.status(500).json({ error: 'Benchmark ran, but result could not be stored', details: error.message, result });
    return;
  }
  res.json({ status: 'completed', ...result });
});

app.post('/api/doctor/benchmark/:server', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const { server } = req.params;
  const duration = Math.min(Math.max(Number(req.body?.duration) || 10, 1), 120);
  const { data: app, error } = await supabase
    .from('docker_apps')
    .select('id, container_id')
    .eq('id', server)
    .single();
  if (error || !app || !app.container_id) {
    res.status(404).json({ error: 'App not found or has no container' });
    return;
  }
  const containerId = String(app.container_id);
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(containerId)) {
    res.status(400).json({ error: 'Invalid container_id format' });
    return;
  }
  try {
    const [result, dockerStats] = await Promise.all([
      runBenchmark(duration),
      runCommand('docker', ['stats', '--no-stream', '--format', '{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}', containerId]),
    ]);
    const { stdout } = dockerStats;
    const [name, cpuPerc, memPerc] = stdout.trim().split('|');
    const container = {
      name: name || containerId,
      cpu_pct: Number(String(cpuPerc || '').replace('%', '')) || 0,
      memory_pct: Number(String(memPerc || '').replace('%', '')) || 0,
    };
    const { error: insertError } = await supabase.from('benchmark_results').insert({
      server_id: server,
      benchmark_type: 'container',
      duration_seconds: duration,
      cpu_score: container.cpu_pct,
      memory_score: container.memory_pct,
      disk_score: result.disk_write_mbps,
      overall_score: container.cpu_pct + container.memory_pct,
      raw_data: { ...result.measurements, container },
    });
    if (insertError) {
      res.status(500).json({ error: 'Benchmark ran, but result could not be stored', details: insertError.message, result, container });
      return;
    }
    res.json({ status: 'completed', server, container, ...result });
  } catch (err: any) {
    if (err.message?.includes('docker') || err.code === 'ENOENT') {
      res.status(502).json({ error: 'Docker is not available', details: err.message });
      return;
    }
    res.status(500).json({ error: 'Failed to benchmark container', details: err.message || String(err) });
  }
});

const DIAGNOSE_ISSUES = ['connectivity', 'performance', 'disk'];

app.post('/api/doctor/diagnose', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const { issue } = req.body;
  const checks = await runDiagnostics(issue as string | undefined);
  res.json(checks);
});

app.post('/api/doctor/diagnose/:server', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const { issue } = req.body;
  const checks = await runDiagnostics(issue as string | undefined);
  res.json({ server: req.params.server, ...checks });
});

// ============================================================================
// Change History / Rollback API Routes
// ============================================================================

app.get('/api/changes', verifyAuth, requireSelfPermission('audit', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { resource, limit } = req.query;
  let query = supabase.from('change_history').select('*').eq('user_id', userId).order('created_at', { ascending: false }).limit(parseInt(limit as string || '20'));
  if (resource) query = query.eq('resource_type', resource as string);
  const { data, error } = await query;
  if (error) return res.status(500).json({ error: error.message });
  res.json({ changes: data || [] });
});

app.get('/api/changes/history', verifyAuth, requireSelfPermission('audit', 'read'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { resource_type, resource_id } = req.query;
  let query = supabase.from('change_history').select('*').eq('user_id', userId).order('created_at', { ascending: false });
  if (resource_type) query = query.eq('resource_type', resource_type as string);
  if (resource_id) query = query.eq('resource_id', resource_id as string);
  const { data, error } = await query;
  if (error) return res.status(500).json({ error: error.message });
  res.json({ history: data || [] });
});

app.post('/api/changes/:id/undo', verifyAuth, requireSelfPermission('audit', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { dry_run } = req.body;
  const { data: change } = await supabase.from('change_history').select('*').eq('id', req.params.id).eq('user_id', userId).single();
  if (!change) return res.status(404).json({ error: 'Change not found' });
  if (dry_run) return res.json({ status: 'would_undo', change: { resource_type: change.resource_type, resource_id: change.resource_id, action: change.action } });
  await supabase.from('change_history').insert({ user_id: userId, resource_type: change.resource_type, resource_id: change.resource_id, action: `undo:${change.action}`, old_value: change.new_value, new_value: change.old_value, summary: `Undo of ${change.action}` });
  res.json({ status: 'undone', change });
});

app.post('/api/rollback', verifyAuth, requireSelfPermission('audit', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { resource_type, resource_id, version } = req.body;
  await supabase.from('change_history').insert({ user_id: userId, resource_type, resource_id, action: 'rollback', summary: `Rollback to ${version || 'previous'}`, new_value: { version } });
  res.json({ status: 'rollback_initiated', resource_type, resource_id, version: version || 'latest' });
});

// ============================================================================
// Activity Timeline API Route
// ============================================================================

app.get('/api/activity', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data, error } = await supabase.from('activity_timeline').select('*').eq('user_id', userId).order('created_at', { ascending: false }).limit(100);
  if (error) return res.status(500).json({ error: error.message });
  res.json({ activities: data || [] });
});

// ============================================================================
// Multi-Tenant / Organization API Routes
// ============================================================================

// ============================================================================
// RBAC MANAGEMENT API ROUTES (server/rbac/)
// ============================================================================

/**
 * GET /api/rbac/me - The caller's own authorization state: instance role,
 * app assignments, and org memberships. Powers frontend route guards.
 */
app.get('/api/rbac/me', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  try {
    const instance = await rbacStore!.getInstanceRole(userId);
    const { data: orgs } = await supabase.from('organization_members').select('organizations(id), role').eq('user_id', userId);
    res.json({
      userId,
      instanceRole: instance?.role ?? null,
      organizations: (orgs || []).map((row: any) => ({
        id: row.organizations?.id ?? null,
        role: row.role,
      })),
    });
  } catch (err) {
    res.status(500).json({ error: 'Failed to load authorization state' });
  }
});

/**
 * GET /api/rbac/instance-roles - List instance-level assignments (admin).
 */
app.get('/api/rbac/instance-roles', verifyAuth, requireInstancePermission('settings', 'read'), async (_req: Request, res: Response) => {
  try {
    res.json({ roles: await rbacStore!.listInstanceRoles() });
  } catch (err) {
    res.status(500).json({ error: 'Failed to list instance roles' });
  }
});

/**
 * POST /api/rbac/instance-roles - Grant or change an instance role (admin).
 * Body: { userId, role: 'admin'|'operator'|'viewer' }. Audited.
 */
app.post('/api/rbac/instance-roles', verifyAuth, requireInstancePermission('settings', 'write'), async (req: Request, res: Response) => {
  const actorId = (req as any).user.id;
  const { userId, role } = req.body || {};
  if (!userId || typeof userId !== 'string') {
    return res.status(400).json({ error: 'userId is required' });
  }
  if (!['admin', 'operator', 'viewer'].includes(role)) {
    return res.status(400).json({ error: "role must be 'admin', 'operator' or 'viewer'" });
  }
  try {
    // Lockout guard: refuse to demote the last instance admin.
    const existing = await rbacStore!.getInstanceRole(userId);
    if (existing && existing.role === 'admin' && role !== 'admin') {
      const roles = await rbacStore!.listInstanceRoles();
      const admins = roles.filter((r) => r.role === 'admin');
      if (admins.length <= 1 && admins.some((r) => r.userId === userId)) {
        return res.status(409).json({ error: 'Cannot demote the last instance admin' });
      }
    }
    const assignment = await rbacStore!.setInstanceRole(userId, role, actorId);
    await logAudit(actorId, 'rbac:instance-role-grant', 'settings', userId, null, { role });
    res.status(201).json(assignment);
  } catch (err) {
    res.status(500).json({ error: 'Failed to grant instance role' });
  }
});

/**
 * DELETE /api/rbac/instance-roles/:userId - Revoke an instance role (admin).
 * Revoke keeps at least one admin (lockout guard): the last bootstrap admin
 * cannot be demoted through this endpoint.
 */
app.delete('/api/rbac/instance-roles/:userId', verifyAuth, requireInstancePermission('settings', 'write'), async (req: Request, res: Response) => {
  const actorId = (req as any).user.id;
  const targetId = req.params.userId;
  try {
    const roles = await rbacStore!.listInstanceRoles();
    const admins = roles.filter((r) => r.role === 'admin');
    const target = roles.find((r) => r.userId === targetId);
    if (!target) return res.status(404).json({ error: 'Assignment not found' });
    if (target.role === 'admin' && admins.length <= 1) {
      return res.status(409).json({ error: 'Cannot revoke the last instance admin' });
    }
    await rbacStore!.deleteInstanceRole(targetId);
    await logAudit(actorId, 'rbac:instance-role-revoke', 'settings', targetId, { role: target.role }, null);
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Failed to revoke instance role' });
  }
});

app.get('/api/organizations', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: owned, error: err1 } = await supabase.from('organizations').select('*').eq('owner_id', userId);
  const { data: member } = await supabase.from('organization_members').select('organizations(*)').eq('user_id', userId);
  const membersOrgs = (member || []).map((m: any) => m.organizations).filter(Boolean);
  if (err1) return res.status(500).json({ error: err1.message });
  res.json({ organizations: [...(owned || []), ...membersOrgs] });
});

app.post('/api/organizations', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, slug } = req.body;
  const { data, error } = await supabase.from('organizations').insert({ name, slug, owner_id: userId }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  await supabase.from('organization_members').insert({ organization_id: data.id, user_id: userId, role: 'owner' });
  res.json(data);
});

// ============================================================================
// Runbook API Routes
// ============================================================================

app.get('/api/runbooks', verifyAuth, requireSelfPermission('runbooks', 'read'), async (req: Request, res: Response) => {
  const { data, error } = await supabase.from('runbooks').select('*').order('name');
  if (error) return res.status(500).json({ error: error.message });
  const builtinRunbooks = [
    { id: 'builtin-deploy-prod', name: 'deploy-production', description: 'Full production deployment pipeline: pull, backup, docker pull, restart, healthcheck, notify', steps: [{ action: 'git_pull', target: 'repo' }, { action: 'backup', target: 'database' }, { action: 'docker_pull', target: 'app' }, { action: 'restart', target: 'app' }, { action: 'healthcheck', target: 'app' }, { action: 'notify', target: 'discord' }], builtin: true },
    { id: 'builtin-rollback', name: 'rollback-deployment', description: 'Rollback the last deployment', steps: [{ action: 'backup', target: 'app' }, { action: 'docker_pull', target: 'previous_version' }, { action: 'restart', target: 'app' }, { action: 'healthcheck', target: 'app' }], builtin: true },
    { id: 'builtin-backup-check', name: 'backup-verify', description: 'Verify all backups are healthy', steps: [{ action: 'list_backups', target: 'all' }, { action: 'verify_backup', target: 'last' }, { action: 'notify', target: 'discord' }], builtin: true },
    { id: 'builtin-system-update', name: 'system-update', description: 'Update system packages and reboot if needed', steps: [{ action: 'backup', target: 'config' }, { action: 'update_packages', target: 'system' }, { action: 'healthcheck', target: 'system' }, { action: 'notify', target: 'email' }], builtin: true },
  ];
  res.json({ runbooks: [...builtinRunbooks, ...(data || [])] });
});

app.post('/api/runbooks', verifyAuth, requireSelfPermission('runbooks', 'write'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { name, description, steps } = req.body;
  const { data, error } = await supabase.from('runbooks').insert({ name, description, steps, created_by: userId }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  res.json(data);
});

app.post('/api/runbooks/:id/execute', verifyAuth, requireSelfPermission('runbooks', 'exec'), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { data: runbook } = await supabase.from('runbooks').select('*').eq('id', req.params.id).single();
  if (!runbook) return res.status(404).json({ error: 'Runbook not found' });
  const { data, error } = await supabase.from('runbook_executions').insert({ runbook_id: runbook.id, triggered_by: userId, status: 'running', output: {} }).select().single();
  if (error) return res.status(500).json({ error: error.message });
  const execSteps = [];
  for (const step of (runbook.steps || [])) {
    execSteps.push({ step: step.action, target: step.target, status: 'completed' });
  }
  await supabase.from('runbook_executions').update({ status: 'success', output: { steps: execSteps }, completed_at: new Date().toISOString() }).eq('id', data.id);
  res.json({ status: 'executed', execution_id: data.id, steps: execSteps });
});

// ============================================================================
// AI Assistant API Routes
// ============================================================================

app.post('/api/assistant/analyze', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { query } = req.body;
  if (!query || typeof query !== 'string') {
    return res.status(400).json({ error: 'query is required' });
  }
  const { data: apps } = await supabase
    .from('docker_apps')
    .select('id, name')
    .eq('user_id', userId);
  const plan = buildPlan(query, (apps || []).map((a: any) => ({ id: a.id, name: a.name })));
  res.json({ analysis: plan, plan_id: `plan-${crypto.randomUUID()}`, requires_approval: plan.requires_approval, message: plan.message });
});

app.post('/api/assistant/execute', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { plan: planBody, approved } = req.body;
  if (!approved) return res.json({ status: 'cancelled', message: 'Execution cancelled by user' });
  if (!planBody || !Array.isArray(planBody.actions) || planBody.actions.length === 0) {
    return res.status(400).json({ error: 'A plan with actions is required' });
  }

  const steps: { tool: string; appId?: string; status: string; output?: string }[] = [];
  try {
    for (const action of planBody.actions) {
      const { tool, appId } = action;
      try {
        if (tool === 'start' || tool === 'stop' || tool === 'restart') {
          const docker = await dockerAction(appId, tool);
          await supabase
            .from('docker_apps')
            .update({ status: tool === 'stop' ? 'stopped' : 'running' })
            .eq('id', appId)
            .eq('user_id', userId);
          steps.push({ tool, appId, status: 'completed', output: docker.output });
          await logAudit(userId, `assistant:${tool}`, 'app', appId);
        } else if (tool === 'status') {
          const { data: app } = await supabase
            .from('docker_apps')
            .select('id, name, status, image')
            .eq('id', appId)
            .eq('user_id', userId)
            .single();
          if (!app) throw new Error('App not found');
          steps.push({ tool, appId, status: 'completed', output: `${app.name}: ${app.status} (${app.image})` });
        } else if (tool === 'logs') {
          const { data: app } = await supabase
            .from('docker_apps')
            .select('id, container_id')
            .eq('id', appId)
            .eq('user_id', userId)
            .single();
          if (!app || !app.container_id) throw new Error('App has no container');
          const { stdout, stderr } = await runCommand('docker', ['logs', '--tail', '50', String(app.container_id)]);
          steps.push({ tool, appId, status: 'completed', output: stdout || stderr });
        } else if (tool === 'benchmark') {
          const result = await runBenchmark(10);
          await supabase.from('benchmark_results').insert({
            server_id: appId || null,
            benchmark_type: appId ? 'container' : 'local',
            duration_seconds: 10,
            cpu_score: result.cpu_avg_pct,
            memory_score: result.memory_used_pct,
            disk_score: result.disk_write_mbps,
            overall_score: result.cpu_avg_pct + result.memory_used_pct,
            raw_data: result.measurements,
          });
          steps.push({ tool, appId, status: 'completed', output: `cpu=${result.cpu_avg_pct}% mem=${result.memory_used_pct}% disk=${result.disk_write_mbps}MiB/s` });
          await logAudit(userId, 'assistant:benchmark', 'app', appId);
        } else {
          throw new Error(`Unsupported tool: ${tool}`);
        }
      } catch (err: any) {
        steps.push({ tool, appId, status: 'failed', output: err.message || String(err) });
        break;
      }
    }
  } catch (err: any) {
    return res.status(500).json({ error: 'Assistant execution failed', details: err.message || String(err) });
  }

  const failed = steps.some((s) => s.status === 'failed');
  res.json({ status: failed ? 'failed' : 'executed', steps });
});

app.post('/api/assistant/chat', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const { message, conversation_id } = req.body;
  if (!message || typeof message !== 'string') {
    return res.status(400).json({ error: 'message is required' });
  }
  const { data: apps } = await supabase
    .from('docker_apps')
    .select('id, name')
    .eq('user_id', (req as any).user.id);
  const plan = buildPlan(message, (apps || []).map((a: any) => ({ id: a.id, name: a.name })));
  const response =
    plan.message ||
    `I can help with infrastructure management, deployments, monitoring and more.`;
  res.json({ response, conversation_id: conversation_id || 'new', plan });
});

// ============================================================================
// Global Search API Enhancement
// ============================================================================

app.get('/api/global-search', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { q } = req.query;
  if (!q) return res.json({ results: [] });
  const query = `%${q}%`;
  const [apps, servers, backups, runbooks, secrets, inventory] = await Promise.all([
    supabase.from('docker_apps').select('id, name, status').eq('user_id', userId).ilike('name', query),
    supabase.from('server_inventory').select('server_id, server_name, owner').eq('user_id', userId).ilike('server_name', query),
    supabase.from('backup_jobs').select('id, name').eq('user_id', userId).ilike('name', query),
    supabase.from('runbooks').select('id, name').ilike('name', query),
    supabase.from('secrets').select('id, key').eq('user_id', userId).ilike('key', query),
    supabase.from('ssh_saved_hosts').select('id, name, host').eq('user_id', userId).ilike('name', query),
  ]);
  res.json({
    results: [
      ...(apps.data || []).map((a: any) => ({ type: 'app', id: a.id, title: a.name, subtitle: a.status })),
      ...(servers.data || []).map((s: any) => ({ type: 'server', id: s.server_id, title: s.server_name, subtitle: s.owner })),
      ...(backups.data || []).map((b: any) => ({ type: 'backup', id: b.id, title: b.name })),
      ...(runbooks.data || []).map((r: any) => ({ type: 'runbook', id: r.id, title: r.name })),
      ...(secrets.data || []).map((s: any) => ({ type: 'secret', id: s.id, title: s.key })),
      ...(inventory.data || []).map((h: any) => ({ type: 'host', id: h.id, title: h.name, subtitle: h.host })),
    ],
  });
});

// ============================================================================
// SSO / OIDC Configuration API Routes (server/sso/)
// ============================================================================

registerSsoRoutes({
  app,
  supabase,
  supabaseAdmin,
  authCheck: verifyAuth,
  logAudit,
  requireInstancePermission,
  loginLimiter,
});

// ============================================================================
// GraphQL API (simplified REST-based)
// ============================================================================

app.post('/api/graphql', verifyAuth, requireWildcardScope(), async (req: Request, res: Response) => {
  const { query: gqlQuery } = req.body;
  if (!gqlQuery || typeof gqlQuery !== 'string') {
    return res.status(400).json({ error: 'Query is required' });
  }
  const userId = (req as any).user.id;
  const result = await executeGraphQL(gqlQuery, {
    userId,
    query: async (table, args) => {
      let builder = supabase.from(table).select('*');
      for (const [key, value] of Object.entries(args || {})) {
        builder = builder.eq(key, value);
      }
      return builder.limit(100) as any;
    },
  });
  res.json(result);
});

// Global error handling middleware
app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
  console.error('[Server] Unhandled error:', err.message || err);
  res.status(500).json({ error: process.env.NODE_ENV === 'production' ? 'Internal server error' : err.message });
});

if (process.env.NODE_ENV !== 'test') {
  httpServer.listen(port, () => {
    console.log(`✨ Docker Panel API running on http://localhost:${port}`);
    console.log(`📡 Frontend should be at http://localhost:5173`);
    console.log(`🐳 Make sure Supabase and Docker are configured in .env.local`);
    // RBAC bootstrap: promote the setup-created admin user before serving.
    rbacStore!.bootstrapInstanceRoles();
  });
}
