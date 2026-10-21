// ────── External secrets: Vault / AWS / Azure references ──────
// Rows with an `external_ref` store no plaintext. Reference syntax:
//   vault://<path>#<key>, aws-sm://<name>, azure://<name>
// Resolution forwards to the orchestrator secrets API (POST
// /api/v1/secrets/get) using the panel's ORCHESTRATOR_URL +
// ORCHESTRATOR_API_TOKEN credential; resolved values live only in a
// short-lived in-process cache and are never logged or persisted.
import axios from 'axios';

const ORCHESTRATOR_URL = process.env.ORCHESTRATOR_URL || 'http://localhost:8500';
const ORCHESTRATOR_API_TOKEN = process.env.ORCHESTRATOR_API_TOKEN || '';
const ORCHESTRATOR_ORG_ID = process.env.ORCHESTRATOR_ORG_ID || 'panel';
const RESOLVE_TIMEOUT_MS = 8000;
const CACHE_TTL_MS = 30000;

const EXTERNAL_REF_PATTERN = /^(vault|aws-sm|azure):\/\/[A-Za-z0-9_/.-]{1,120}(#.?[A-Za-z0-9_-]{1,80})?$/;
const cache = new Map<string, { value: string; backend: string; at: number }>();

export const isExternalRef = (ref: unknown): ref is string =>
  typeof ref === 'string' && EXTERNAL_REF_PATTERN.test(ref);

export const parseExternalRef = (
  ref: string
): { backend: 'vault' | 'aws-sm' | 'azure'; path: string; key?: string } | null => {
  if (!isExternalRef(ref)) return null;
  const [schemePart, ...rest] = ref.split('://');
  const joined = rest.join('://');
  const hashIndex = joined.indexOf('#');
  if (hashIndex === -1) return { backend: schemePart as any, path: joined };
  return {
    backend: schemePart as any,
    path: joined.slice(0, hashIndex),
    key: joined.slice(hashIndex + 1) || undefined,
  };
};

const cacheGet = (orgId: string, ref: string) => {
  const hit = cache.get(`${orgId}:${ref}`);
  if (hit && Date.now() - hit.at < CACHE_TTL_MS) return hit;
  cache.delete(`${orgId}:${ref}`);
  return null;
};

const orchPost = async (path: string, body: Record<string, unknown>, actorUserId: string) => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (ORCHESTRATOR_API_TOKEN) headers.Authorization = `Bearer ${ORCHESTRATOR_API_TOKEN}`;
  if (actorUserId) headers['X-Actor-User-Id'] = actorUserId;
  const response = await axios.post(`${ORCHESTRATOR_URL}${path}`, body, {
    headers,
    timeout: RESOLVE_TIMEOUT_MS,
    validateStatus: () => true,
  });
  return response;
};

export const orchestratorSecretsConfigured = () => Boolean(ORCHESTRATOR_API_TOKEN);

export const orchestratorStatus = async (): Promise<{
  orchestratedReachable: boolean;
  backend: string;
  configured: boolean;
}> => {
  if (!ORCHESTRATOR_API_TOKEN) {
    return { orchestratedReachable: false, backend: 'none', configured: false };
  }
  try {
    const response = await axios.get(`${ORCHESTRATOR_URL}/api/v1/federation/status`, {
      headers: { Authorization: `Bearer ${ORCHESTRATOR_API_TOKEN}` },
      timeout: RESOLVE_TIMEOUT_MS,
      validateStatus: () => true,
    });
    if (response.status !== 200 || typeof response.data !== 'object') {
      return { orchestratedReachable: false, backend: 'unknown', configured: true };
    }
    return {
      orchestratedReachable: true,
      backend: (response.data as any).secrets_backend || (response.data as any).backend || 'unknown',
      configured: true,
    };
  } catch {
    return { orchestratedReachable: false, backend: 'unknown', configured: true };
  }
};

export const resolveExternalSecret = async (
  ref: string,
  actorUserId: string
): Promise<{ value: string; backend: string } | null> => {
  const parsed = parseExternalRef(ref);
  if (!parsed) return null;
  const cached = cacheGet(ORCHESTRATOR_ORG_ID, ref);
  if (cached) return { value: cached.value, backend: cached.backend };
  if (!ORCHESTRATOR_API_TOKEN) return null;
  const body: Record<string, unknown> = {
    org_id: ORCHESTRATOR_ORG_ID,
    path: parsed.path,
    actor_user_id: actorUserId || 'panel',
  };
  if (parsed.key) body.key = parsed.key;
  try {
    const response = await orchPost('/api/v1/secrets/get', body, actorUserId);
    if (response.status !== 200 || !response.data || typeof response.data.value !== 'string') {
      return null;
    }
    const entry = {
      value: response.data.value,
      backend: parsed.backend as string,
      at: Date.now(),
    };
    cache.set(`${ORCHESTRATOR_ORG_ID}:${ref}`, entry);
    return { value: entry.value, backend: entry.backend };
  } catch (err: any) {
    console.error('External secret resolution failed:', err?.message || err);
    return null;
  }
};

export const rotateExternalSecret = async (
  ref: string,
  actorUserId: string
): Promise<{ backend: string } | null> => {
  const parsed = parseExternalRef(ref);
  if (!parsed) return null;
  if (!ORCHESTRATOR_API_TOKEN) return null;
  const body: Record<string, unknown> = {
    org_id: ORCHESTRATOR_ORG_ID,
    path: parsed.path,
    actor_user_id: actorUserId || 'panel',
  };
  cache.delete(`${ORCHESTRATOR_ORG_ID}:${ref}`);
  try {
    const response = await orchPost('/api/v1/secrets/rotate', { org_id: ORCHESTRATOR_ORG_ID, path: parsed.path }, actorUserId);
    if (response.status !== 200 && response.status !== 201) return null;
    return { backend: parsed.backend as string };
  } catch (err: any) {
    console.error('External secret rotation failed:', err?.message || err);
    return null;
  }
};
