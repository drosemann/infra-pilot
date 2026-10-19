/**
 * Minimal OIDC authorization-code + PKCE client.
 *
 * Implemented with Node `crypto` plus the global `fetch` already used
 * elsewhere in the panel — no OAuth framework dependency. Only the
 * pieces the panel actually uses are implemented:
 *
 * - discovery (`/.well-known/openid-configuration`) with a short cache
 * - authorization URL building (PKCE S256 + state + nonce)
 * - authorization-code exchange
 * - id_token verification (RS256 via JWKS) with iss/aud/exp/nonce checks
 * - optional userinfo fetch
 * - HS256 compact JWS sign/verify for panel session tokens
 *
 * Deliberately NOT implemented: SAML assertion handling (documented as
 * roadmap work), client_assertion/private_key_jwt, JWE, HS/ES-signed
 * id_tokens.
 */

import { createHash, createHmac, createPublicKey, verify as cryptoVerify, randomBytes, timingSafeEqual } from 'crypto';

export interface OIDCProviderConfig {
  id: string;
  name: string;
  issuerUrl(): string | null;
  clientId(): string | null;
  clientSecret(): string | null;
}

export interface OIDCWellKnown {
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  userinfo_endpoint?: string;
  jwks_uri: string;
}

export interface PkcePair {
  verifier: string;
  challenge: string;
}

export interface IdTokenClaims {
  iss: string;
  sub: string;
  aud: string | string[];
  exp: number;
  iat?: number;
  nonce?: string;
  email?: string;
  email_verified?: boolean;
  preferred_username?: string;
  name?: string;
  groups?: string[];
}

/** Provider registry. Env-driven; a provider without client id is not usable. */
export const OIDC_PROVIDERS: OIDCProviderConfig[] = [
  {
    id: 'google',
    name: 'Google',
    issuerUrl: () => process.env.GOOGLE_ISSUER_URL || 'https://accounts.google.com',
    clientId: () => process.env.GOOGLE_CLIENT_ID || null,
    clientSecret: () => process.env.GOOGLE_CLIENT_SECRET || null,
  },
  {
    id: 'microsoft',
    name: 'Microsoft Entra ID',
    issuerUrl: () => {
      const tenant = process.env.MICROSOFT_TENANT_ID;
      return tenant
        ? `https://login.microsoftonline.com/${tenant}/v2.0`
        : (process.env.MICROSOFT_ISSUER_URL || null);
    },
    clientId: () => process.env.MICROSOFT_CLIENT_ID || null,
    clientSecret: () => process.env.MICROSOFT_CLIENT_SECRET || null,
  },
  {
    id: 'oidc',
    name: 'Generic OIDC',
    issuerUrl: () => process.env.OIDC_ISSUER_URL || null,
    clientId: () => process.env.OIDC_CLIENT_ID || null,
    clientSecret: () => process.env.OIDC_CLIENT_SECRET || null,
  },
];

const DISCOVERY_TTL_MS = 10 * 60 * 1000;
const discoveryCache = new Map<string, { wellKnown: OIDCWellKnown; fetchedAt: number }>();
const jwksCache = new Map<string, { jwks: { keys: Array<Record<string, string>> }; fetchedAt: number }>();

function fail(message: string): never {
  throw new Error(message);
}

/** Whether the provider has the env vars needed to run a flow. */
export function providerUsable(config: OIDCProviderConfig): boolean {
  const issuer = config.issuerUrl();
  return Boolean(issuer && config.clientId() && config.clientSecret());
}

/** Redirect URI the IdP must be configured with for this panel install. */
export function redirectUri(providerId: string, baseUrl: string): string {
  return `${baseUrl.replace(/\/+$/, '')}/api/sso/callback/${providerId}`;
}

/** Fetch (and cache) the issuer's OpenID discovery document. */
export async function discover(issuerUrl: string): Promise<OIDCWellKnown> {
  const cached = discoveryCache.get(issuerUrl);
  if (cached && Date.now() - cached.fetchedAt < DISCOVERY_TTL_MS) {
    return cached.wellKnown;
  }
  const url = `${issuerUrl.replace(/\/+$/, '')}/.well-known/openid-configuration`;
  const response = await fetch(url, { signal: AbortSignal.timeout(10_000) });
  if (!response.ok) {
    fail(`OIDC discovery failed for ${issuerUrl}: HTTP ${response.status}`);
  }
  const body = (await response.json()) as Partial<OIDCWellKnown>;
  if (!body.authorization_endpoint || !body.token_endpoint || !body.jwks_uri || !body.issuer) {
    fail(`OIDC discovery for ${issuerUrl} is missing required endpoints`);
  }
  const wellKnown: OIDCWellKnown = {
    issuer: body.issuer as string,
    authorization_endpoint: body.authorization_endpoint as string,
    token_endpoint: body.token_endpoint as string,
    userinfo_endpoint: body.userinfo_endpoint,
    jwks_uri: body.jwks_uri as string,
  };
  discoveryCache.set(issuerUrl, { wellKnown, fetchedAt: Date.now() });
  return wellKnown;
}

/** Base64url helpers (Node buffer, no extra dependency). */
function b64url(input: Buffer): string {
  return input.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function b64urlJson(obj: unknown): string {
  return b64url(Buffer.from(JSON.stringify(obj), 'utf8'));
}
function fromCustomBase64(segment: string): Buffer {
  const normalized = segment.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
  return Buffer.from(padded, 'base64');
}

/** Create a PKCE S256 pair (RFC 7636). */
export function createPkcePair(): PkcePair {
  const verifier = b64url(randomBytes(32)); // 43 chars, url-safe
  const challenge = b64url(createHash('sha256').update(verifier).digest());
  return { verifier, challenge };
}

/**
 * Build the authorization redirect URL. The caller persists
 * `{ state, nonce, verifier }` server-side and validates them at callback.
 */
export function buildAuthorizationUrl(
  wellKnown: OIDCWellKnown,
  config: OIDCProviderConfig,
  params: {
    state: string;
    nonce: string;
    codeChallenge: string;
    redirectUri: string;
  },
): string {
  const url = new URL(wellKnown.authorization_endpoint);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('client_id', config.clientId() as string);
  url.searchParams.set('redirect_uri', params.redirectUri);
  url.searchParams.set('scope', 'openid email profile groups');
  url.searchParams.set('state', params.state);
  url.searchParams.set('nonce', params.nonce);
  url.searchParams.set('code_challenge', params.codeChallenge);
  url.searchParams.set('code_challenge_method', 'S256');
  return url.toString();
}

/** Exchange the authorization code for tokens at the token endpoint. */
export async function exchangeCode(
  wellKnown: OIDCWellKnown,
  config: OIDCProviderConfig,
  params: { code: string; redirectUri: string; codeVerifier: string },
): Promise<{ id_token?: string; access_token?: string; refresh_token?: string; expires_in?: number }> {
  const response = await fetch(wellKnown.token_endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json' },
    signal: AbortSignal.timeout(15_000),
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code: params.code,
      redirect_uri: params.redirectUri,
      client_id: config.clientId() as string,
      client_secret: config.clientSecret() as string,
      code_verifier: params.codeVerifier,
    }).toString(),
  });
  if (!response.ok) {
    const detail = await response.text().catch(() => '');
    fail(`Token exchange failed: HTTP ${response.status}${detail.slice(0, 200)}`);
  }
  return (await response.json()) as { id_token?: string; access_token?: string };
}

/** Fetch the issuer's JSON Web Key Set (cached at DISCOVERY_TTL_MS). */
export async function fetchJwks(jwksUri: string): Promise<{ keys: Array<Record<string, string>> }> {
  const cached = jwksCache.get(jwksUri);
  if (cached && Date.now() - cached.fetchedAt < DISCOVERY_TTL_MS) {
    return cached.jwks;
  }
  const response = await fetch(jwksUri, { signal: AbortSignal.timeout(10_000) });
  if (!response.ok) {
    fail(`JWKS fetch failed for ${jwksUri}: HTTP ${response.status}`);
  }
  const jwks = (await response.json()) as { keys: Array<Record<string, string>> };
  jwksCache.set(jwksUri, { jwks, fetchedAt: Date.now() });
  return jwks;
}

function parseCompactJwt(token: string): {
  header: Record<string, string>;
  payload: Record<string, any>;
  signingInput: Buffer;
  signature: Buffer;
} {
  const parts = token.split('.');
  if (parts.length !== 3) {
    fail('Malformed id_token');
  }
  const [h, p, s] = parts;
  let header: Record<string, string>;
  let payload: Record<string, any>;
  try {
    header = JSON.parse(fromCustomBase64(h).toString('utf8')) as Record<string, string>;
    payload = JSON.parse(fromCustomBase64(p).toString('utf8')) as Record<string, any>;
  } catch {
    fail('Malformed id_token encoding');
  }
  return {
    header,
    payload,
    signingInput: Buffer.from(`${h}.${p}`),
    signature: fromCustomBase64(s),
  };
}

/**
 * Verify an RS256-signed id_token against the issuer's JWKS and validate
 * standard claims (exp with 30s skew, iss, aud, nonce, sub). Throws on any
 * failure; returns the decoded claims on success.
 */
export async function verifyIdToken(
  idToken: string,
  expected: { issuerUrl: string; audience: string; nonce?: string },
): Promise<IdTokenClaims> {
  const wellKnown = await discover(expected.issuerUrl);
  const { header, payload, signingInput, signature } = parseCompactJwt(idToken);
  if (header.alg !== 'RS256') {
    fail(`Unsupported id_token alg ${String(header.alg)} (only RS256 is supported)`);
  }
  const jwks = await fetchJwks(wellKnown.jwks_uri);
  const kid = header.kid;
  const candidates = jwks.keys.filter(
    (key) => key.kty === 'RSA' && (kid ? key.kid === kid : true) && key.n && key.e,
  );
  if (candidates.length === 0) {
    fail('No matching RSA key in JWKS for id_token');
  }
  let verified = false;
  for (const jwk of candidates) {
    try {
      const key = createPublicKey({
        key: { kty: jwk.kty, n: jwk.n, e: jwk.e },
        format: 'jwk',
      });
      verified = cryptoVerify('RSA-SHA256', signingInput, key, signature);
      if (verified) break;
    } catch {
      // try next candidate key
    }
  }
  if (!verified) {
    fail('id_token signature verification failed');
  }
  const claims = payload as unknown as IdTokenClaims;
  if (typeof claims.exp !== 'number' || claims.exp * 1000 < Date.now() - 30_000) {
    fail('id_token expired');
  }
  // Allow either the configured issuer or the one advertised by discovery
  // (some IdPs advertise with different trailing-slash/tenant normalization).
  const configured = expected.issuerUrl.replace(/\/+$/, '');
  const advertised = wellKnown.issuer.replace(/\/+$/, '');
  const tokenIss = (claims.iss || '').replace(/\/+$/, '');
  if (tokenIss !== configured && tokenIss !== advertised) {
    fail(`id_token issuer mismatch: ${tokenIss}`);
  }
  const audOk = Array.isArray(claims.aud)
    ? claims.aud.includes(expected.audience)
    : claims.aud === expected.audience;
  if (!audOk) {
    fail('id_token audience mismatch');
  }
  if (expected.nonce && claims.nonce !== expected.nonce) {
    fail('id_token nonce mismatch');
  }
  if (!claims.sub) {
    fail('id_token missing sub claim');
  }
  return claims;
}

/** Fetch userinfo when the IdP exposes it (throws on error). */
export async function fetchUserinfo(
  userinfoEndpoint: string,
  accessToken: string,
): Promise<Record<string, any>> {
  const response = await fetch(userinfoEndpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    fail(`Userinfo fetch failed: HTTP ${response.status}`);
  }
  return (await response.json()) as Record<string, any>;
}

/** Sign a compact HS256 JWS — used for panel session tokens. */
export function signCompactHS256(payload: unknown, secret: string): string {
  const header = { alg: 'HS256', typ: 'JWT' };
  const b64Payload = b64url(Buffer.from(typeof payload === 'string' ? payload : JSON.stringify(payload), 'utf8'));
  const signingInput = `${b64urlJson(header)}.${b64Payload}`;
  const mac = b64url(createHmac('sha256', secret).update(signingInput).digest());
  return `${signingInput}.${mac}`;
}

/** Verify and decode an HS256 compact JWS produced by signCompactHS256. */
export function verifyCompactHS256(token: string, secret: string): Record<string, any> | null {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  const [h, p, s] = parts;
  const signingInput = `${h}.${p}`;
  const macBuf = fromCustomBase64(s);
  const expectedBuf = createHmac('sha256', secret).update(signingInput).digest();
  if (macBuf.length !== expectedBuf.length || !timingSafeEqual(macBuf, expectedBuf)) return null;
  let payload: Record<string, any>;
  try {
    payload = JSON.parse(fromCustomBase64(p).toString('utf8')) as Record<string, any>;
  } catch {
    return null;
  }
  return payload;
}
