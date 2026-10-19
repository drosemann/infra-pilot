/**
 * SSO state, session, and identity persistence.
 *
 * Three stores live here:
 *
 * 1. Authorization "flights" — in-memory, single-use state/nonce/PKCE
 *    verifier pairs that survive for 10 minutes. Deliberately bounded to
 *    the panel process (documented limitation; horizontal deployments
 *    need a shared store or sticky routing until PROMPT 8 lands Redis).
 * 2. Panel sessions — DB rows (`panel_sessions` in db/schema.sql) that
 *    back both the `ip_session` cookie and the `sso_...` Bearer token
 *    verifyAuth accepts.
 * 3. Identities — `sso_identities` rows mapping (provider, sub) to a
 *    Supabase auth user, created JIT-provisioned with the service-role
 *    client, gated by the email/domain allowlists.
 */

import { createHmac, randomBytes, timingSafeEqual } from 'crypto';

export const SESSION_COOKIE_NAME = 'ip_session';
export const SESSION_TTL_MS = Math.min(
  Math.max(Number(process.env.PANEL_SESSION_TTL_HOURS || 12), 1),
  7 * 24,
) * 60 * 60 * 1000;

export interface SsoSessionRow {
  id: string;
  user_id: string;
  provider: string;
  expires_at: string;
  revoked: boolean;
  created_at?: string;
  last_seen_at?: string;
}

export interface SsoIdentityRow {
  id: string;
  provider: string;
  sub: string;
  email: string;
  email_verified: boolean;
  display_name?: string | null;
  user_id: string;
  groups: string[] | null;
  last_login_at?: string;
  created_at?: string;
}

export interface SsoFlight {
  providerId: string;
  state: string;
  nonce: string;
  verifier: string;
  createdAt: number;
}

function fail(message: string): never {
  throw new Error(message);
}

function sessionSecret(): string {
  const secret = process.env.SESSION_SECRET || '';
  if (!secret || secret === 'CHANGE_ME_SESSION_SECRET') {
    fail('SESSION_SECRET is not configured; SSO sessions are disabled');
  }
  return secret;
}

/* ============================================================
 * Authorization flights (state + nonce + PKCE verifier)
 * ============================================================ */

const flights = new Map<string, SsoFlight>();
const FLIGHT_TTL_MS = 10 * 60 * 1000;
const FLIGHT_MAX = 1000;

/** Persist a new authorization flight; returns the state token. */
export function startFlight(flight: SsoFlight): string {
  // Bound memory: drop expired + oldest entries first.
  sweepFlights();
  if (flights.size >= FLIGHT_MAX) {
    const oldest = [...flights.values()]
      .sort((a, b) => a.createdAt - b.createdAt)[0];
    if (oldest) flights.delete(oldest.state);
  }
  flights.set(flight.state, flight);
  return flight.state;
}

/** Consume a flight exactly once; null when unknown or expired. */
export function consumeFlight(state: string): SsoFlight | null {
  const flight = flights.get(state);
  flights.delete(state); // single-use regardless of outcome
  if (!flight) return null;
  if (Date.now() - flight.createdAt > FLIGHT_TTL_MS) return null;
  return flight;
}

function sweepFlights(): void {
  const now = Date.now();
  for (const [state, flight] of flights) {
    if (now - flight.createdAt > FLIGHT_TTL_MS) flights.delete(state);
  }
}

/* ============================================================
 * Session tokens: DB-backed, HMAC-signed, cookie + Bearer
 * ============================================================ */

export interface SessionClientLike {
  from(table: string): any;
}

/**
 * HMAC over the session id. Authorization tokens carry
 * `sso_<sessionId>.<mac>`; the DB row remains the source of truth
 * (revocation, expiry, provider attribution).
 */
function sessionMac(sessionId: string, secret: string): Buffer {
  return createHmac('sha256', secret).update(sessionId).digest();
}

/** Split `sso_<sessionId>.<mac>` into its parts. */
function parseSessionToken(token: string): { sessionId: string; mac: Buffer } | null {
  if (typeof token !== 'string' || !token.startsWith('sso_')) return null;
  const rest = token.slice(4);
  const dot = rest.lastIndexOf('.');
  if (dot <= 0) return null;
  const sessionId = rest.slice(0, dot);
  const rawMac = rest.slice(dot + 1).replace(/-/g, '+').replace(/_/g, '/');
  const mac = Buffer.from(rawMac + '='.repeat((4 - (rawMac.length % 4)) % 4), 'base64');
  if (!/^[0-9a-f-]{36}$/.test(sessionId)) return null;
  return { sessionId, mac };
}

/**
 * Create a panel session row and return the token string usable as a
 * Bearer token (`sso_...`) and as the cookie value.
 */
export async function createSession(
  supabase: SessionClientLike,
  params: { userId: string; provider: string; expiresAt?: Date | null },
): Promise<{ token: string; sessionId: string; expiresAt: Date }> {
  const secret = sessionSecret();
  const ttl = params.expiresAt
    ? Math.min(params.expiresAt.getTime(), Date.now() + SESSION_TTL_MS)
    : Date.now() + SESSION_TTL_MS;
  const expiresAt = new Date(ttl);
  const { data, error } = await (supabase as any)
    .from('panel_sessions')
    .insert({ user_id: params.userId, provider: params.provider, expires_at: expiresAt.toISOString(), revoked: false })
    .select('id')
    .single();
  if (error || !data) {
    fail(`Failed to persist panel session: ${error?.message || 'no row returned'}`);
  }
  const sessionId = data.id as string;
  const mac = sessionMac(sessionId, secret);
  const token = `sso_${sessionId}.${mac.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')}`;
  return { token, sessionId, expiresAt };
}

/**
 * Validate a session token (Bearer `sso_...` form). Returns the row or
 * null. Hook-shop: never throws — auth failures are just "not ours".
 */
export async function resolveSessionToken(
  supabase: SessionClientLike,
  token: string,
): Promise<SsoSessionRow | null> {
  try {
    const secret = sessionSecret();
    const parsed = parseSessionToken(token);
    if (!parsed) return null;
    if (!timingSafeEqual(parsed.mac, sessionMac(parsed.sessionId, secret))) return null;
    const { data, error } = await (supabase as any)
      .from('panel_sessions')
      .select('id, user_id, provider, expires_at, revoked')
      .eq('id', parsed.sessionId)
      .maybeSingle();
    if (error || !data) return null;
    const row = data as SsoSessionRow;
    if (row.revoked) return null;
    if (row.expires_at && new Date(row.expires_at).getTime() < Date.now()) {
      // Lazy GC of an expired row.
      void (supabase as any).from('panel_sessions').delete().eq('id', row.id);
      return null;
    }
    void (supabase as any)
      .from('panel_sessions')
      .update({ last_seen_at: new Date().toISOString() })
      .eq('id', row.id);
    return row;
  } catch {
    return null;
  }
}

/** Revoke exactly one session. */
export async function revokeSession(supabase: SessionClientLike, sessionId: string): Promise<void> {
  await (supabase as any).from('panel_sessions').update({ revoked: true }).eq('id', sessionId);
}

/** Revoke every session a user holds (used at logout-all / RBAC churn). */
export async function revokeAllSessionsForUser(
  supabase: SessionClientLike,
  userId: string,
): Promise<void> {
  await (supabase as any).from('panel_sessions').update({ revoked: true }).eq('user_id', userId);
}

/* ============================================================
 * Cookie helpers (no cookie-parser dependency)
 * ============================================================ */

/** Parse a Cookie header into a map of the panel's interest. */
export function parseCookies(header: string | undefined): Record<string, string> {
  const out: Record<string, string> = {};
  if (!header) return out;
  for (const part of header.split(';')) {
    const eq = part.indexOf('=');
    if (eq <= 0) continue;
    const name = part.slice(0, eq).trim();
    let value = part.slice(eq + 1).trim();
    if (value.startsWith('"') && value.endsWith('"')) value = value.slice(1, -1);
    try {
      out[name] = decodeURIComponent(value);
    } catch {
      out[name] = value;
    }
  }
  return out;
}

/** Cookie attributes: httpOnly, SameSite=Lax, Secure in production. */
export function sessionCookieOptions(expiresAt: Date) {
  return {
    httpOnly: true,
    sameSite: 'lax' as const,
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: Math.max(0, expiresAt.getTime() - Date.now()) / 1000,
  };
}

/* ============================================================
 * Identities: JIT provisioning + email/domain allowlists
 * ============================================================ */

export interface SupabaseAdminLike {
  auth: {
    admin: {
      listUsers(options?: any): Promise<any>;
      createUser(attrs: any): Promise<any>;
    };
  };
  from(table: string): any;
}

/** Whether email is admitted by the allowlists (unset = any address). */
export function emailAllowed(email: string): boolean {
  const exact = (process.env.SSO_EMAIL_ALLOWLIST || '')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
  const domains = (process.env.SSO_EMAIL_DOMAIN_ALLOWLIST || '')
    .split(',')
    .map((s) => s.trim().toLowerCase().replace(/^@/, ''))
    .filter(Boolean);
  if (exact.length === 0 && domains.length === 0) return true;
  if (exact.includes(email.toLowerCase())) return true;
  const domain = email.toLowerCase().split('@')[1] || '';
  return domains.length > 0 && domains.includes(domain);
}

/** Enumerate auth users in pages until the email matches (bounded). */
async function findAuthUserByEmail(
  admin: SupabaseAdminLike,
  email: string,
): Promise<any | null> {
  let page = 1;
  for (let i = 0; i < 50; i += 1) {
    const { data, error } = await admin.auth.admin.listUsers({ page, perPage: 200 });
    if (error || !data?.users) return null;
    const match = data.users.find((u: any) => (u.email || '').toLowerCase() === email.toLowerCase());
    if (match) return match;
    if (data.users.length < 200) return null;
    page += 1;
  }
  return null;
}

export interface IdentityResolution {
  userId: string;
  identityId: string;
  isNew: boolean;
  /** Instance role applied from group mapping, when one was set. */
  roleApplied: null | 'admin' | 'operator' | 'viewer';
}

/**
 * Resolve (and JIT-provision when needed) the panel identity behind an
 * OIDC login. Returns the Supabase user id the panel works with.
 */
export async function resolveIdentity(
  supabaseAdmin: SupabaseAdminLike,
  params: {
    provider: string;
    sub: string;
    email: string;
    emailVerified: boolean;
    displayName?: string;
    groups: string[];
  },
): Promise<IdentityResolution> {
  if (!params.emailVerified) {
    fail('IdP did not verify the email address; JIT provisioning refused');
  }
  if (!emailAllowed(params.email)) {
    fail('Email address is not permitted by the configured SSO allowlists');
  }

  const { data: existing, error: existingError } = await supabaseAdmin
    .from('sso_identities')
    .select('*')
    .eq('provider', params.provider)
    .eq('sub', params.sub)
    .maybeSingle();
  if (existingError) {
    fail(`Identity lookup failed: ${existingError.message}`);
  }

  let userId: string;
  let identityId: string;
  let isNew = false;

  if (existing) {
    userId = (existing as SsoIdentityRow).user_id;
    identityId = (existing as SsoIdentityRow).id;
    await supabaseAdmin
      .from('sso_identities')
      .update({
        email: params.email,
        email_verified: params.emailVerified,
        display_name: params.displayName || null,
        groups: params.groups,
        last_login_at: new Date().toISOString(),
      })
      .eq('id', identityId);
  } else {
    isNew = true;
    let authUser = await findAuthUserByEmail(supabaseAdmin, params.email);
    if (!authUser) {
      const displayName = params.displayName || params.email.split('@')[0];
      const { data: created, error: createError } = await supabaseAdmin.auth.admin.createUser({
        email: params.email,
        email_confirm: true,
        // Random secret the user never sees: SSO is the only way in for
        // JIT identities; password login would require a Supabase reset.
        password: randomBytes(32).toString('hex'),
        user_metadata: { display_name: displayName, sso_provider: params.provider },
      });
      if (createError || !created?.user) {
        fail(`JIT provisioning failed: ${createError?.message || 'no user returned'}`);
      }
      authUser = created.user;
    }
    userId = authUser.id as string;
    const { data: identityRow, error: identityError } = await supabaseAdmin
      .from('sso_identities')
      .insert({
        provider: params.provider,
        sub: params.sub,
        email: params.email,
        email_verified: params.emailVerified,
        display_name: params.displayName || null,
        user_id: userId,
        groups: params.groups,
        last_login_at: new Date().toISOString(),
      })
      .select('id')
      .single();
    if (identityError || !identityRow) {
      fail(`Failed to persist SSO identity: ${identityError?.message || 'no row returned'}`);
    }
    identityId = identityRow.id as string;
  }

  const roleApplied = await applyGroupRoleMapping(supabaseAdmin, {
    provider: params.provider,
    userId,
    groups: params.groups,
  });

  return { userId, identityId, isNew, roleApplied };
}

const ROLE_RANK: Record<string, number> = { viewer: 1, operator: 2, admin: 3 };

/**
 * Apply the best group→instance-role mapping for the user. Only applies
 * when the user has NO existing instance role: admin-set roles always win.
 */
async function applyGroupRoleMapping(
  supabaseAdmin: SupabaseAdminLike,
  params: { provider: string; userId: string; groups: string[] },
): Promise<IdentityResolution['roleApplied']> {
  if (params.groups.length === 0) return null;
  const { data: mappings, error } = await supabaseAdmin
    .from('sso_group_roles')
    .select('group_name, role')
    .eq('provider', params.provider);
  if (error || !mappings) return null;
  const userGroups = new Set(params.groups.map((g) => String(g)));
  let best: { role: string; rank: number } | null = null;
  for (const mapping of mappings as Array<{ group_name: string; role: string }>) {
    if (!userGroups.has(mapping.group_name)) continue;
    const role = String(mapping.role).toLowerCase();
    if (!(role in ROLE_RANK)) continue;
    if (!best || ROLE_RANK[role] > best.rank) best = { role, rank: ROLE_RANK[role] };
  }
  if (!best) return null;
  const { data: current } = await supabaseAdmin
    .from('rbac_instance_roles')
    .select('role')
    .eq('user_id', params.userId)
    .maybeSingle();
  if (current) return null; // never downgrade or fight a human decision
  await supabaseAdmin
    .from('rbac_instance_roles')
    .insert({ user_id: params.userId, role: best.role, granted_by: null })
    .select('id')
    .single();
  return best.role as IdentityResolution['roleApplied'];
}
