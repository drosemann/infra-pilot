/**
 * @file Typed client for the panel feature-flag evaluate endpoint.
 * The browser only ever receives resolved values, never targeting rules.
 */

import { apiClient } from './api';

export type FlagKey = 'discord_service_v2' | 'living_fleet' | (string & {});

interface EvaluateResponse {
  evaluatedAt: string;
  environment: string;
  flags: Record<string, boolean | string>;
}

let cache: { at: number; flags: Record<string, boolean | string> } | null = null;
const TTL_MS = 30_000;

export async function fetchEvaluatedFlags(force = false): Promise<Record<string, boolean | string>> {
  if (!force && cache && Date.now() - cache.at < TTL_MS) return cache.flags;
  const res = await (apiClient as any).api.get<EvaluateResponse>('/api/feature-flags/evaluate');
  cache = { at: Date.now(), flags: res.data.flags || {} };
  return cache.flags;
}

export function readCachedFlag(key: string, fallback: boolean | string = false): boolean | string {
  if (cache && key in cache.flags) return cache.flags[key];
  return envFlagOverride(key, fallback);
}

/** Local escape hatch for dev/incidents: VITE_FEATURE_FLAG_<KEY>. */
export function envFlagOverride(key: string, fallback: boolean | string): boolean | string {
  try {
    const raw = (import.meta as any).env?.[`VITE_FEATURE_FLAG_${key.toUpperCase().replace(/[^A-Z0-9]/g, '_')}`];
    if (raw === 'true') return true;
    if (raw === 'false') return false;
    if (raw !== undefined) return raw;
  } catch {
    // non-browser / no env — fall through
  }
  return fallback;
}

let flagSocket: WebSocket | null = null;

/** Open the WS invalidation channel; server pushes nudge, we refetch over HTTP. */
export function subscribeFlagUpdates(): () => void {
  try {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${window.location.host}?channel=feature-flags`);
    flagSocket = ws;
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'feature-flags:changed') {
          window.dispatchEvent(new CustomEvent('feature-flags:changed', { detail: msg }));
        }
      } catch {
        // ignore malformed nudges; TTL polling still converges
      }
    };
    return () => {
      try { ws.close(); } catch { /* already closed */ }
      if (flagSocket === ws) flagSocket = null;
    };
  } catch {
    return () => {};
  }
}

export function invalidateFlagCache(): void {
  cache = null;
}
