/** Feature-flag client for the Discord service (read-only consumer). */
const PanelUrl = process.env.FEATURE_FLAGS_PANEL_URL || 'http://localhost:3001';
const PollSeconds = Number(process.env.FEATURE_FLAGS_POLL_SECONDS || 30);
const ServiceToken = process.env.FEATURE_FLAGS_SERVICE_TOKEN || '';

const cache = new Map();
let timer = null;

async function refresh() {
  if (!process.env.FEATURE_FLAGS_ENABLED || process.env.FEATURE_FLAGS_ENABLED === 'false') return;
  try {
    const res = await fetch(`${PanelUrl}/api/feature-flags/evaluate`, {
      headers: ServiceToken ? { Authorization: `Bearer ${ServiceToken}` } : {},
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return;
    const data = await res.json();
    for (const [k, v] of Object.entries(data.flags || {})) cache.set(k, v);
  } catch {
    // Panel unreachable: keep last-known values, fall back to defaults below.
  }
}

function start() {
  if (timer || !process.env.FEATURE_FLAGS_ENABLED || process.env.FEATURE_FLAGS_ENABLED === 'false') return;
  refresh();
  timer = setInterval(refresh, PollSeconds * 1000);
  if (timer.unref) timer.unref();
}

function envOverride(key) {
  const envKey = `FEATURE_FLAG_${key.toUpperCase().replace(/[^A-Z0-9]/g, '_')}`;
  const raw = process.env[envKey];
  if (raw === undefined) return null;
  const v = String(raw).trim().toLowerCase();
  if (v === 'true') return true;
  if (v === 'false') return false;
  return raw;
}

/** Never throws; returns default when the flag is unknown or the panel is down. */
function isEnabled(key, defaultValue = false) {
  try {
    const ov = envOverride(key);
    if (ov !== null) return ov;
    if (cache.has(key)) return cache.get(key);
    return defaultValue;
  } catch {
    return defaultValue;
  }
}

module.exports = { start, refresh, isEnabled };
