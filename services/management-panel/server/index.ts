import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';
import http from 'http';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import path from 'path';
import { promises as fs } from 'fs';

dotenv.config({ path: '.env.local' });

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const port = process.env.PORT || 3001;

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
app.post('/api/setup/init', async (req: Request, res: Response) => {
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
// DOCKER APP ROUTES (require auth)
// ============================================================================

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
  const { name, image, ports, environmentVars, volumes, memoryLimit, cpuShares, description } = req.body;

  if (!name || !image) {
    return res.status(400).json({ error: 'Name and image are required' });
  }

  try {
    const { data, error } = await supabase
      .from('docker_apps')
      .insert({
        user_id: userId,
        name,
        image,
        status: 'stopped',
        ports: ports || [],
        environment_vars: environmentVars || {},
        volumes: volumes || [],
        memory_limit: memoryLimit,
        cpu_shares: cpuShares,
        description,
      })
      .select()
      .single();

    if (error) throw error;
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

  try {
    const { data, error } = await supabase
      .from('docker_apps')
      .update(req.body)
      .eq('id', appId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'App not found' });
    }

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
    // Fetch app details
    const { data: app, error: fetchError } = await supabase
      .from('docker_apps')
      .select('*')
      .eq('id', appId)
      .eq('user_id', userId)
      .single();

    if (fetchError || !app) {
      return res.status(404).json({ error: 'App not found' });
    }

    // TODO: Integrate with Docker API to actually start container
    // For now, just update status in DB
    const { data, error } = await supabase
      .from('docker_apps')
      .update({
        status: 'running',
        started_at: new Date().toISOString(),
      })
      .eq('id', appId)
      .select()
      .single();

    if (error) throw error;
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to start app' });
  }
});

// POST /api/apps/:appId/stop - Stop a container
app.post('/api/apps/:appId/stop', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const { data, error } = await supabase
      .from('docker_apps')
      .update({ status: 'stopped' })
      .eq('id', appId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'App not found' });
    }

    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to stop app' });
  }
});

// POST /api/apps/:appId/restart - Restart a container
app.post('/api/apps/:appId/restart', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;

  try {
    const { data, error } = await supabase
      .from('docker_apps')
      .update({
        status: 'restarting',
      })
      .eq('id', appId)
      .eq('user_id', userId)
      .select()
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'App not found' });
    }

    // TODO: Trigger actual Docker restart, then update status to running
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to restart app' });
  }
});

// GET /api/apps/:appId/logs - Stream logs (paginated)
app.get('/api/apps/:appId/logs', verifyAuth, async (req: Request, res: Response) => {
  const userId = (req as any).user.id;
  const { appId } = req.params;
  const limit = Math.min(parseInt(req.query.limit as string) || 50, 1000);
  const offset = parseInt(req.query.offset as string) || 0;

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

    // Fetch logs
    const { data, error } = await supabase
      .from('app_logs')
      .select('*')
      .eq('app_id', appId)
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1);

    if (error) throw error;
    res.json(data || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch logs' });
  }
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

// Health check with basic instrumentation exposure
app.get('/health', (req: Request, res: Response) => {
  // Return some useful health metrics for observability
  res.json({ status: 'ok', uptime: process.uptime(), version: APP_VERSION, metrics });
});

// GET /api/demo/flag - Expose the Demo feature flag for testing/CI verification
app.get('/api/demo/flag', (_req: Request, res: Response) => {
  const enabled = process.env.VITE_DEMO_FEATURE_ENABLED === 'true';
  res.json({ enabled });
});

// Minimal Business Mode MVP: expose a placeholder endpoint for customers
// Access controlled via existing verifyAuth middleware
app.get('/api/customers', verifyAuth, async (req: Request, res: Response) => {
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
app.post('/api/customers', verifyAuth, async (req: Request, res: Response) => {
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

if (process.env.NODE_ENV !== 'test') {
  app.listen(port, () => {
    console.log(`✨ Docker Panel API running on http://localhost:${port}`);
    console.log(`📡 Frontend should be at http://localhost:5173`);
    console.log(`🐳 Make sure Supabase and Docker are configured in .env.local`);
  });
}
