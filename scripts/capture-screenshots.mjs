/**
 * Capture real management-panel screenshots with Playwright.
 *
 * Requires: Node 22+, `npm install`, running panel stack.
 * Usage:
 *   npm run dev &
 *   node scripts/capture-screenshots.mjs
 *
 * Output: docs/screenshots/*.png (1600x900).
 * Mask secrets before committing.
 */
import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, '../docs/screenshots');
const BASE = process.env.PANEL_URL || 'http://localhost:5173';

const shots = [
  { route: '/dashboard', file: '01-dashboard.png' },
  { route: '/monitoring', file: '02-monitoring.png' },
  { route: '/apps', file: '03-applications.png' },
  { route: '/backups', file: '04-backups.png' },
  { route: '/settings', file: '05-cli-gitops.png' },
];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });

for (const s of shots) {
  await page.goto(`${BASE}${s.route}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(OUT, s.file) });
  console.log(`captured ${s.file}`);
}

await browser.close();
