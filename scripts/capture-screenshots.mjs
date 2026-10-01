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
    let data = {};
    if (url.pathname === '/health') data = { status: 'ok' };
    else if (url.pathname === '/api/setup/status') data = { initialized: true, mode: 'business' };
    else if (url.pathname === '/api/user') data = { id: 'demo-admin', email: 'admin@example.com', display_name: 'Demo Admin', role: 'Admin' };
    else if (url.pathname === '/api/apps') data = apps;
    else if (url.pathname.startsWith('/api/apps/')) data = apps[0];
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
