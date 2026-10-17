/**
 * Short-lived, single-purpose WebSocket tickets.
 *
 * Format: `wst1.<base64url(claims)>.<base64url(HMAC-SHA256)>`
 *
 * Properties:
 * - Bound to a user id (`uid`) and optionally a single app (`aid`).
 * - Single use: the nonce (`n`) is consumed on first successful verification,
 *   so a captured ticket cannot be replayed (replay window is bounded by the
 *   ticket expiry, so the nonce store stays small).
 * - Revocable by `jti`, or wholesale per user (revokes every ticket minted
 *   before the revocation instant).
 * - Signature comparison is constant time; ticket strings are never logged.
 */
import crypto from 'crypto';
import type { Clock, MintedTicket, TicketClaims, VerifyResult } from './types.ts';

const TICKET_VERSION = 'wst1';
const NONCE_BYTES = 16;
const JTI_BYTES = 12;
const MIN_CLAIM_STRING_LENGTH = 8;
const SIGNATURE_BYTES = 32;

export interface TicketServiceOptions {
  /** HMAC-SHA256 key; see `resolveWsTicketSecret` in `config.ts`. */
  secret: string;
  /** Ticket lifetime in seconds (enforced <= 300 by config validation). */
  ttlSeconds?: number;
  /** Clock-skew tolerance in seconds for nbf/exp checks. */
  skewSeconds?: number;
  clock?: Clock;
}

export interface MintOptions {
  appId?: string;
}

/**
 * Mints and verifies WS tickets. One instance per process; verification state
 * (nonces, revocations) intentionally lives in memory because tickets are
 * short-lived and the panel runs as a single service.
 */
export class TicketService {
  private readonly key: Buffer;
  private readonly ttlSeconds: number;
  private readonly skewSeconds: number;
  private readonly clock: Clock;
  /** nonce -> absolute expiry ms (kept until the ticket itself is dead). */
  private readonly nonces = new Map<string, number>();
  /** jti -> absolute expiry ms. */
  private readonly revokedJti = new Map<string, number>();
  /** userId -> revocation instant (fractional epoch seconds). */
  private readonly revokedUsers = new Map<string, number>();

  constructor(options: TicketServiceOptions) {
    if (!options.secret || options.secret.length < 16) {
      throw new Error('TicketService requires a secret of at least 16 characters');
    }
    this.key = Buffer.from(options.secret, 'utf8');
    this.ttlSeconds = options.ttlSeconds ?? 300;
    this.skewSeconds = options.skewSeconds ?? 30;
    this.clock = options.clock ?? Date.now;
  }

  private sign(data: string): string {
    return crypto.createHmac('sha256', this.key).update(data, 'utf8').digest('base64url');
  }

  /**
   * Mint a ticket for a user.
   * @param userId - Subject of the ticket
   * @param options - Optional single-app scope
   * @returns The ticket string and its claims (claims include the raw `jti`)
   * @throws Error when `userId` or `appId` are invalid
   */
  mint(userId: string, options?: MintOptions): MintedTicket {
    if (typeof userId !== 'string' || userId.trim() === '') {
      throw new Error('Cannot mint a WS ticket without a user id');
    }
    const nowMs = this.clock();
    const nowSec = nowMs / 1000;
    const claims: TicketClaims = {
      uid: userId,
      nbf: nowSec,
      exp: nowSec + this.ttlSeconds,
      n: crypto.randomBytes(NONCE_BYTES).toString('base64url'),
      jti: crypto.randomBytes(JTI_BYTES).toString('base64url'),
    };
    if (options?.appId !== undefined) {
      if (typeof options.appId !== 'string' || options.appId.trim() === '') {
        throw new Error('Ticket appId scope must be a non-empty string');
      }
      if (options.appId.length > 128) {
        throw new Error('Ticket appId scope must be at most 128 characters');
      }
      claims.aid = options.appId;
    }
    const payload = Buffer.from(JSON.stringify(claims), 'utf8').toString('base64url');
    const signed = `${TICKET_VERSION}.${payload}`;
    return { ticket: `${signed}.${this.sign(signed)}`, claims };
  }

  private decodeAndCheckShape(parts: string[]): TicketClaims | null {
    const [, payload] = parts;
    try {
      const json = Buffer.from(payload, 'base64url').toString('utf8');
      const claims = JSON.parse(json) as Partial<TicketClaims>;
      if (
        typeof claims.uid !== 'string' ||
        claims.uid.trim() === '' ||
        typeof claims.n !== 'string' ||
        claims.n.length < MIN_CLAIM_STRING_LENGTH ||
        typeof claims.jti !== 'string' ||
        claims.jti.length < MIN_CLAIM_STRING_LENGTH ||
        typeof claims.nbf !== 'number' ||
        !Number.isFinite(claims.nbf) ||
        typeof claims.exp !== 'number' ||
        !Number.isFinite(claims.exp)
      ) {
        return null;
      }
      if (claims.aid !== undefined && (typeof claims.aid !== 'string' || claims.aid.length > 128)) {
        return null;
      }
      return claims as TicketClaims;
    } catch {
      return null;
    }
  }

  private verifyParts(
    ticket: unknown,
    markNonce: boolean,
  ): VerifyResult {
    if (typeof ticket !== 'string' || ticket.length === 0 || ticket.length > 4096) {
      return { ok: false, reason: 'malformed' };
    }
    const parts = ticket.split('.');
    if (parts.length !== 3 || parts[0] !== TICKET_VERSION || !parts[1] || !parts[2]) {
      return { ok: false, reason: 'malformed' };
    }
    const claims = this.decodeAndCheckShape(parts);
    if (!claims) {
      return { ok: false, reason: 'malformed' };
    }
    const expected = Buffer.from(this.sign(`${parts[0]}.${parts[1]}`), 'base64url');
    const actual = Buffer.from(parts[2], 'base64url');
    if (
      actual.length !== expected.length ||
      actual.length !== SIGNATURE_BYTES ||
      !crypto.timingSafeEqual(actual, expected)
    ) {
      return { ok: false, reason: 'bad_signature' };
    }

    const nowSec = this.clock() / 1000;
    const skew = this.skewSeconds;
    if (nowSec > claims.exp + skew) {
      return { ok: false, reason: 'expired', claims };
    }
    if (nowSec < claims.nbf - skew) {
      return { ok: false, reason: 'not_yet_valid', claims };
    }
    const revokedAt = this.revokedUsers.get(claims.uid);
    if (revokedAt !== undefined && claims.nbf <= revokedAt) {
      return { ok: false, reason: 'revoked', claims };
    }
    const jtiExpiry = this.revokedJti.get(claims.jti);
    if (jtiExpiry !== undefined && jtiExpiry > this.clock()) {
      return { ok: false, reason: 'revoked', claims };
    }
    if (markNonce) {
      const nonceExpiry = this.nonces.get(claims.n);
      if (nonceExpiry !== undefined && nonceExpiry > this.clock()) {
        return { ok: false, reason: 'replayed', claims };
      }
      // Keep the nonce until the ticket itself can no longer be presented.
      this.nonces.set(claims.n, claims.exp * 1000 + skew * 1000);
    }
    return { ok: true, claims };
  }

  /**
   * Fully verify a ticket, consuming its nonce (replay protection).
   * @param ticket - Candidate ticket from `?ticket=` or an `auth` message
   */
  verify(ticket: unknown): VerifyResult {
    return this.verifyParts(ticket, true);
  }

  /**
   * Verify signature, shape, time, and revocation WITHOUT consuming the nonce.
   * Used by the revoke endpoint, where presenting the ticket is not a use.
   */
  inspect(ticket: unknown): VerifyResult {
    return this.verifyParts(ticket, false);
  }

  /**
   * Revoke a single ticket by id until the given instant.
   * @param jti - Ticket id from the claims
   * @param untilMs - Absolute expiry (defaults to TTL from now)
   */
  revoke(jti: string, untilMs?: number): void {
    if (typeof jti !== 'string' || jti.length === 0) return;
    const expiry = untilMs ?? this.clock() + this.ttlSeconds * 1000;
    this.revokedJti.set(jti, expiry);
  }

  /**
   * Revoke every ticket a user was issued before now. Tickets minted after
   * this call remain valid (fractional-second resolution).
   */
  revokeAllForUser(userId: string): void {
    if (typeof userId !== 'string' || userId.length === 0) return;
    this.revokedUsers.set(userId, this.clock() / 1000);
  }

  /** True when the user currently has a standing revocation. */
  isUserRevoked(userId: string): boolean {
    return this.revokedUsers.has(userId);
  }

  /**
   * Drop nonce and revocation entries whose tickets can no longer verify.
   * @returns Number of entries removed
   */
  sweep(nowMs?: number): number {
    const now = nowMs ?? this.clock();
    let removed = 0;
    for (const [key, expiry] of this.nonces) {
      if (expiry <= now) {
        this.nonces.delete(key);
        removed += 1;
      }
    }
    for (const [key, expiry] of this.revokedJti) {
      if (expiry <= now) {
        this.revokedJti.delete(key);
        removed += 1;
      }
    }
    for (const [key, revokedAt] of this.revokedUsers) {
      // Revocation only needs to outlive the longest possible ticket.
      if (revokedAt * 1000 + (this.ttlSeconds + this.skewSeconds) * 1000 <= now) {
        this.revokedUsers.delete(key);
        removed += 1;
      }
    }
    return removed;
  }

  /** Introspection for tests and diagnostics; never expose in API responses. */
  stateSizes(): { nonces: number; revokedJti: number; revokedUsers: number } {
    return {
      nonces: this.nonces.size,
      revokedJti: this.revokedJti.size,
      revokedUsers: this.revokedUsers.size,
    };
  }
}
