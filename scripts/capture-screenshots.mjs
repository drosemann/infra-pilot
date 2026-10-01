/**
 * Capture real management-panel screenshots with Playwright.
 *
 * Requires: Node 22+, `npm install`, and the local Vite frontend.
 * Usage:
 *   npm run dev:frontend &
 *   node scripts/capture-screenshots.mjs
 *
 * Output: docs/screenshots/*.png (1600x900).
 * Mask secrets before committing.
 */
import { createRequire } from 'module';
import path from 'path';
import { fileURLToPath } from 'url';
import { mkdir } from 'fs/promises';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(path.resolve(__dirname, '../services/management-panel/package.json'));
const { chromium } = require('playwright');
const OUT = path.resolve(__dirname, '../docs/screenshots');
const BASE = process.env.PANEL_URL || 'http://localhost:5173';
// Mirrors the frontend default (VITE_API_URL || 'http://localhost:3001' in src/lib/api.ts).
const API_BASE = process.env.VITE_API_URL || 'http://localhost:3001';
const NAVIGATION_ATTEMPTS = 5;
const NAVIGATION_RETRY_DELAY_MS = 2000;
const NAVIGATION_TIMEOUT_MS = 30_000;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const shots = [
  { route: '/dashboard', file: '01-dashboard.png' },
  { route: '/monitoring', file: '02-monitoring.png' },
  { route: '/apps/shop-api', file: '03-applications.png' },
  { route: '/backups', file: '04-backups.png' },
  { route: '/settings', file: '05-cli-gitops.png' },
];

await mkdir(OUT, { recursive: true });
const browser = await chromium.launch();

// Capture mode uses safe, representative demo responses and never requires a
// running local backend or an authenticated account.
async function mockDemoApi(context) {
  await context.addInitScript(() => localStorage.setItem('sb_access_token', 'screenshot-demo-token'));
  await context.route(`${API_BASE}/**`, async (route) => {
    const url = new URL(route.request().url());
    const apps = [
      { id: 'shop-api', name: 'shop-api', image: 'ghcr.io/acme/shop-api:stable', status: 'running', created_at: '2026-09-15T10:00:00Z', ports: [{ hostPort: 8080, containerPort: 8080, protocol: 'tcp' }] },
      { id: 'web', name: 'customer-portal', image: 'ghcr.io/acme/customer-portal:stable', status: 'running', created_at: '2026-09-12T08:30:00Z', ports: [{ hostPort: 3000, containerPort: 3000, protocol: 'tcp' }] },
      { id: 'worker', name: 'jobs-worker', image: 'ghcr.io/acme/jobs-worker:stable', status: 'stopped', created_at: '2026-09-10T14:00:00Z', ports: [] },
    ];
    const backupJobs = [
      { id: 'job-shop-daily', user_id: 'demo-admin', app_id: 'shop-api', name: 'shop-api daily', schedule_type: 'daily', retention_count: 7, next_run: '2026-10-02T03:00:00Z', last_run: '2026-10-01T03:00:00Z', status: 'active', created_at: '2026-09-15T10:00:00Z' },
      { id: 'job-portal-weekly', user_id: 'demo-admin', app_id: 'web', name: 'customer-portal weekly', schedule_type: 'weekly', retention_count: 4, next_run: '2026-10-05T04:00:00Z', last_run: '2026-09-28T04:00:00Z', status: 'active', created_at: '2026-09-12T08:30:00Z' },
    ];
    const backupEntries = {
      'job-shop-daily': [
        { id: 1, backup_job_id: 'job-shop-daily', status: 'success', size_mb: 288.6, error_message: '', started_at: '2026-09-30T03:00:00Z', completed_at: '2026-09-30T03:04:12Z' },
        { id: 2, backup_job_id: 'job-shop-daily', status: 'success', size_mb: 291.8, error_message: '', started_at: '2026-09-29T03:00:00Z', completed_at: '2026-09-29T03:04:40Z' },
        { id: 3, backup_job_id: 'job-shop-daily', status: 'failed', size_mb: 0, error_message: 'snapshot timeout', started_at: '2026-09-28T03:00:00Z', completed_at: '2026-09-28T03:02:11Z' },
        { id: 4, backup_job_id: 'job-shop-daily', status: 'success', size_mb: 301.9, error_message: '', started_at: '2026-09-27T03:00:00Z', completed_at: '2026-09-27T03:05:02Z' },
      ],
      'job-portal-weekly': [
        { id: 5, backup_job_id: 'job-portal-weekly', status: 'success', size_mb: 402.4, error_message: '', started_at: '2026-09-28T04:00:00Z', completed_at: '2026-09-28T04:09:41Z' },
        { id: 6, backup_job_id: 'job-portal-weekly', status: 'success', size_mb: 398.1, error_message: '', started_at: '2026-09-21T04:00:00Z', completed_at: '2026-09-21T04:09:05Z' },
      ],
    };
  let data = {};
  if (url.pathname === '/health') data = { status: 'ok' };
  else if (url.pathname === '/api/setup/status') data = { initialized: true, mode: 'business' };
  else if (url.pathname === '/api/user') data = { id: 'demo-admin', email: 'admin@example.com', display_name: 'Demo Admin', role: 'Admin' };
  else if (url.pathname === '/api/apps') data = apps;
  else if (url.pathname.startsWith('/api/apps/')) data = apps[0];
  else if (url.pathname === '/api/backup-jobs') data = backupJobs;
  else if (url.pathname.startsWith('/api/backup-jobs/')) data = backupEntries[url.pathname.split('/')[3]] || [];
  else if (url.pathname === '/api/maintenance-windows') data = [];
    else if (url.pathname.includes('/metrics') || url.pathname.includes('/backups') || url.pathname.includes('/logs')) data = [];
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
  });
}

async function gotoWithRetry(page, url) {
  for (let attempt = 1; attempt <= NAVIGATION_ATTEMPTS; attempt += 1) {
    try {
      return await page.goto(url, {
        waitUntil: 'networkidle',
        timeout: NAVIGATION_TIMEOUT_MS,
      });
    } catch (error) {
      if (attempt === NAVIGATION_ATTEMPTS) {
        throw error;
      }

      console.warn(
        `navigation attempt ${attempt} failed for ${url}; retrying in ${NAVIGATION_RETRY_DELAY_MS}ms`,
      );
      await sleep(NAVIGATION_RETRY_DELAY_MS);
    }
  }
}

// A fresh browser context per shot keeps mocks, storage, and UI state hermetic:
// reusing one page across navigations breaks API interception on later shots,
// and the onboarding tour overlay would otherwise block sidebar interaction.
for (const s of shots) {
  const context = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  await mockDemoApi(context);
  const page = await context.newPage();
  await gotoWithRetry(page, `${BASE}${s.route}`);
  // Dismiss the first-run tour so captures show the UI, then expand sidebar
  // groups so beta badges on nested items are visible.
  try {
    await page.getByRole('button', { name: 'Skip' }).click({ timeout: 3000 });
  } catch {
    // No tour overlay on this route.
  }
  for (const group of ['Logs', 'Reports', 'Settings']) {
    try {
      await page.getByRole('button', { name: group }).first().click({ timeout: 2000 });
    } catch {
      // Group already expanded or not rendered on this route.
    }
  }
  await sleep(1500);
  await page.screenshot({ path: path.join(OUT, s.file) });
  console.log(`captured ${s.file}`);
  await context.close();
}

await browser.close();
