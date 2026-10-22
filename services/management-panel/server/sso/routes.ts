/**
 * SSO / OIDC HTTP routes.
 *
 * Mounted by `server/index.ts`. Login and callback are browser redirects;
 * everything else speaks JSON. SAML is intentionally NOT implemented —
 * `GET /api/sso/saml` answers 501 with a roadmap note so nobody confuses
 * a stub with a working integration.
 */

import { Request, Response } from 'express';
import rateLimit from 'express-rate-limit';
import { randomBytes } from 'crypto';
import {
  OIDC_PROVIDERS,
  buildAuthorizationUrl,
  createPkcePair,
  discover,
  exchangeCode,
  fetchUserinfo,
  providerUsable,
  redirectUri,
  verifyIdToken,
} from './oidc.ts';
import {
  SESSION_COOKIE_NAME,
  createSession,
  consumeFlight,
  parseCookies,
  resolveSessionToken,
  revokeSession,
  sessionCookieOptions,
  startFlight,
  resolveIdentity,
  type SupabaseAdminLike,
} from './store.ts';

interface SsoDeps {
  app: { get(path: string, ...handlers: any[]): void; post(path: string, ...handlers: any[]): void; put(path: string, ...handlers: any[]): void; delete(path: string, ...handlers: any[]): void };
  supabase: any;
  supabaseAdmin: SupabaseAdminLike | null;
  authCheck: (req: any, res: any, next: () => void) => Promise<void> | void;
  logAudit: (...args: any[]) => Promise<void>;
  requireInstancePermission: (resourceType: string, action: string) => any;
  loginLimiter: any;
}

/** Derive the externally visible base URL (proxy-aware, no headers spoof). */
function baseUrlFor(req: Request): string {
  if (process.env.PANEL_PUBLIC_URL) {
    return process.env.PANEL_PUBLIC_URL.replace(/\/+$/, '');
  }
  const protoHeader = String(req.headers['x-forwarded-proto'] || req.protocol || 'http');
  const proto = protoHeader.split(',')[0].trim();
  const host = String(req.headers['x-forwarded-host'] || req.headers.host || `localhost:${process.env.PORT || 3001}`);
  return `${proto}://${host}`;
}

/** Where the SPA lives (SSO callbacks hand the session token to it). */
function frontendUrlFor(req: Request): string {
  if (process.env.PANEL_FRONTEND_URL) {
    return process.env.PANEL_FRONTEND_URL.replace(/\/+$/, '');
  }
  if (process.env.PANEL_PUBLIC_URL) {
    return process.env.PANEL_PUBLIC_URL.replace(/\/+$/, '');
  }
  return baseUrlFor(req);
}

function providerFor(id: string) {
  return OIDC_PROVIDERS.find((p) => p.id === id) || null;
}

/**
 * Register every SSO route on the panel's Express app.
 */
export function registerSsoRoutes(deps: SsoDeps): void {
  const { app, supabase, supabaseAdmin, authCheck, logAudit, requireInstancePermission, loginLimiter } = deps;
  const ssoRouteLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
  });

  /**
   * GET /api/sso/providers - which identity providers are configured and
   * usable. Public: returns only booleans/ids, never secrets.
   */
  app.get('/api/sso/providers', (_req: Request, res: Response) => {
    const providers = OIDC_PROVIDERS.map((provider) => ({
      id: provider.id,
      name: provider.name,
      enabled: providerUsable(provider),
    }));
    // GitHub uses OAuth2 without id_tokens; a row appears only when the
    // operator configures an OIDC-compatible gateway for it.
    const githubConfigured = Boolean(process.env.GITHUB_CLIENT_ID);
    if (githubConfigured) {
      providers.push({
        id: 'github',
        name: 'GitHub',
        // GitHub's OAuth2 app flow has no id_token; it cannot run through
        // the OIDC flow below and is therefore never enabled here.
        enabled: false,
      });
    }
    res.json({
      providers,
      saml: { enabled: false, note: 'SAML is not implemented; see the SSO roadmap in the README.' },
    });
  });

  /**
   * GET /api/sso/saml - explicit 501 rather than a fake endpoint.
   */
  app.get('/api/sso/saml', (_req: Request, res: Response) => {
    res.status(501).json({
      error: 'SAML is not implemented yet',
      note: 'OIDC is the shipped SSO path. Signed SAML Response verification is documented as roadmap work (see README and wiki/11-Auth-Matrix.md).',
    });
  });

  /**
   * GET /api/sso/login/:providerId - start the authorization-code flow
   * (302 to the IdP). Requires SPA base URL configuration in production.
   */
  app.get('/api/sso/login/:providerId', ssoRouteLimiter, loginLimiter, async (req: Request, res: Response) => {
    const provider = providerFor(req.params.providerId);
    if (!provider) {
      return res.status(404).json({ error: 'Unknown SSO provider' });
    }
    if (!providerUsable(provider)) {
      return res.status(503).json({ error: `Provider ${provider.id} is not configured (client id or secrets missing)` });
    }
    try {
      const issuerUrl = provider.issuerUrl() as string;
      const wellKnown = await discover(issuerUrl);
      const pkce = createPkcePair();
      const state = randomBytes(24).toString('hex');
      const nonce = randomBytes(24).toString('hex');
      startFlight({ providerId: provider.id, state, nonce, verifier: pkce.verifier, createdAt: Date.now() });
      const url = buildAuthorizationUrl(wellKnown, provider, {
        state,
        nonce,
        codeChallenge: pkce.challenge,
        redirectUri: redirectUri(provider.id, baseUrlFor(req)),
      });
      return res.redirect(302, url);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'SSO provider discovery failed';
      return res.status(502).json({ error: message });
    }
  });

  /**
   * GET /api/sso/callback/:providerId - code consumer. Validates state +
   * nonce, verifies the id_token against JWKS, provisions/links the
   * identity, and issues a panel session (cookie + Bearer token handed to
   * the SPA via the URL fragment).
   */
  app.get('/api/sso/callback/:providerId', ssoRouteLimiter, loginLimiter, async (req: Request, res: Response) => {
    const provider = providerFor(req.params.providerId);
    const frontendUrl = frontendUrlFor(req);
    const back = (reason: string) => `/#sso_error=${encodeURIComponent(reason)}`;
    try {
      if (!provider) {
        return res.redirect(302, back('Unknown SSO provider'));
      }
      if (!providerUsable(provider)) {
        return res.redirect(302, back('SSO provider not configured'));
      }
      const { code, state } = req.query as { code?: string; state?: string };
      const errorParam = (req.query as { error?: string }).error;
      if (errorParam) {
        return res.redirect(302, back(`Identity provider error: ${errorParam}`));
      }
      if (!code || !state) {
        return res.redirect(302, back('Missing code or state parameter'));
      }
      const flight = consumeFlight(String(state));
      if (!flight || flight.providerId !== provider.id) {
        return res.redirect(302, back('Invalid or expired login state'));
      }
      const issuerUrl = provider.issuerUrl() as string;
      const wellKnown = await discover(issuerUrl);
      const tokens = await exchangeCode(wellKnown, provider, {
        code: String(code),
        redirectUri: redirectUri(provider.id, baseUrlFor(req)),
        codeVerifier: flight.verifier,
      });
      if (!tokens.id_token) {
        return res.redirect(302, back('Provider did not return an id_token (not OIDC-compatible)'));
      }
      const claims = await verifyIdToken(tokens.id_token, {
        issuerUrl,
        audience: provider.clientId() as string,
        nonce: flight.nonce,
      });
      let email = claims.email || '';
      let emailVerified = claims.email_verified === true;
      let displayName = claims.name || claims.preferred_username || '';
      let groups = Array.isArray(claims.groups) ? claims.groups.map(String) : [];
      if ((!email || !emailVerified) && wellKnown.userinfo_endpoint && tokens.access_token) {
        const info = await fetchUserinfo(wellKnown.userinfo_endpoint, tokens.access_token);
        email = info.email || email;
        if (typeof info.email_verified === 'boolean') emailVerified = info.email_verified;
        groups = Array.isArray(info.groups) ? info.groups.map(String) : groups;
      }
      if (!email) {
        return res.redirect(302, back('Provider did not return an email claim'));
      }
      if (process.env.NODE_ENV === 'production' && !process.env.SESSION_SECRET) {
        return res.redirect(302, back('Server is missing SESSION_SECRET; SSO disabled'));
      }
      if (!supabaseAdmin) {
        return res.redirect(302, back('SUPABASE_SERVICE_ROLE_KEY is required for SSO identity linking/JIT provisioning'));
      }
      const identity = await resolveIdentity(supabaseAdmin, {
        provider: provider.id,
        sub: claims.sub,
        email,
        emailVerified,
        displayName: displayName || undefined,
        groups,
      });
      const session = await createSession(supabase, {
        userId: identity.userId,
        provider: provider.id,
        expiresAt: null,
      });
      await logAudit(identity.userId, 'sso:login', 'identity', identity.identityId, null, {
        provider: provider.id,
        isNew: identity.isNew,
      });
      res.clearCookie(SESSION_COOKIE_NAME, { path: '/' });
      res.cookie(SESSION_COOKIE_NAME, session.token, sessionCookieOptions(session.expiresAt));
      return res.redirect(302, `${frontendUrl}/#sso_token=${encodeURIComponent(session.token)}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'SSO callback failed';
      console.error('[sso] callback error:', message);
      return res.redirect(302, back(message));
    }
  });

  /**
   * GET /api/sso/session - who the authed caller is and how they
   * authenticated (JWT/API key vs SSO session).
   */
  app.get('/api/sso/session', authCheck, async (req: Request, res: Response) => {
    const authMethod = (req as any).authMethod || 'none';
    const body: Record<string, unknown> = {
      user: (req as any).user?.id ?? null,
      method: authMethod,
    };
    if (authMethod === 'sso-session') {
      body.provider = (req as any).session?.provider ?? null;
      body.expiresAt = (req as any).session?.expires_at ?? null;
    }
    res.json(body);
  });

  /**
   * POST /api/sso/logout - revoke the current SSO session (when the
   * caller authenticated through one) and clear the cookie.
   */
  app.post('/api/sso/logout', deps.authCheck, async (req: Request, res: Response) => {
    const cookies = parseCookies(req.headers.cookie);
    const cookieToken = cookies[SESSION_COOKIE_NAME];
    if (cookieToken && (req as any).authMethod !== 'sso-session') {
      // Cookie may belong to a different session than the Bearer token.
      const row = await resolveSessionToken(supabase, cookieToken);
      if (row) {
        await revokeSession(supabase, row.id);
        await logAudit(row.user_id, 'sso:logout', 'session', row.id, null, { provider: row.provider });
      }
    }
    if ((req as any).authMethod === 'sso-session' && (req as any).session?.id) {
      await revokeSession(supabase, (req as any).session.id);
      await logAudit((req as any).user.id, 'sso:logout', 'session', (req as any).session.id, null, {
        provider: (req as any).session.provider,
      });
    }
    res.clearCookie(SESSION_COOKIE_NAME, { httpOnly: true, sameSite: 'lax', secure: process.env.NODE_ENV === 'production', path: '/' });
    res.json({ success: true });
  });

  /*
   * Group → instance-role mapping administration (RBAC: instance admin).
   */

  /**
   * GET /api/sso/group-roles - list configured mappings.
   */
  app.get('/api/sso/group-roles', deps.authCheck, requireInstancePermission('settings', 'read'), async (_req: Request, res: Response) => {
    const { data, error } = await supabase.from('sso_group_roles').select('*').order('provider').order('group_name');
    if (error) {
      return res.status(500).json({ error: 'Failed to list group role mappings' });
    }
    res.json({ mappings: data || [] });
  });

  /**
   * PUT /api/sso/group-roles - upsert one mapping { provider, group, role }.
   * Audited; persisted in `sso_group_roles` (db/schema.sql).
   */
  app.put('/api/sso/group-roles', deps.authCheck, requireInstancePermission('settings', 'write'), async (req: Request, res: Response) => {
    const actorId = (req as any).user.id;
    const { provider, group, role } = req.body || {};
    const normalizedRole = String(role || '').toLowerCase();
    const providerId = providerFor(String(provider || ''));
    if (!providerId || String(provider) === 'github') {
      return res.status(400).json({ error: "provider must be one of 'google', 'microsoft', 'oidc'" });
    }
    if (!group || typeof group !== 'string' || group.length > 200) {
      return res.status(400).json({ error: 'group is required (<= 200 chars)' });
    }
    if (!['admin', 'operator', 'viewer'].includes(normalizedRole)) {
      return res.status(400).json({ error: "role must be 'admin', 'operator' or 'viewer'" });
    }
    const { data, error } = await supabase
      .from('sso_group_roles')
      .upsert(
        { provider: provider.id, group_name: group, role: normalizedRole },
        { onConflict: 'provider,group_name' },
      )
      .select()
      .single();
    if (error) {
      return res.status(500).json({ error: 'Failed to save group role mapping' });
    }
    await logAudit(actorId, 'sso:group-role-map', 'settings', `${provider.id}:${group}`, null, { role: normalizedRole });
    res.status(201).json(data);
  });

  /**
   * DELETE /api/sso/group-roles - remove one mapping { provider, group }.
   */
  app.delete('/api/sso/group-roles', deps.authCheck, requireInstancePermission('settings', 'write'), async (req: Request, res: Response) => {
    const actorId = (req as any).user.id;
    const provider = providerFor(String(req.body?.provider || ''));
    const group = req.body?.group;
    if (!provider || !group || typeof group !== 'string') {
      return res.status(400).json({ error: 'provider and group are required' });
    }
    const { data, error } = await supabase
      .from('sso_group_roles')
      .delete()
      .eq('provider', provider.id)
      .eq('group_name', group)
      .select();
    if (error) {
      return res.status(500).json({ error: 'Failed to delete group role mapping' });
    }
    if (!data || data.length === 0) {
      return res.status(404).json({ error: 'Mapping not found' });
    }
    await logAudit(actorId, 'sso:group-role-unmap', 'settings', `${provider.id}:${group}`, null, null);
    res.json({ success: true });
  });
}
