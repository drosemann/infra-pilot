/**
 * Token-bucket rate limiting for the WebSocket gateway.
 *
 * Two scopes exist:
 * - `messages`: per-connection budget for all inbound frames
 * - `subscribe`: per-user budget for log/metric subscription attempts
 *
 * Denied attempts increment a strike counter; a connection that exhausts its
 * strikes is closed with WS_CLOSE_CODES.RATE_LIMITED. Buckets are pruned by
 * `sweep()` so idle connections do not leak memory.
 */
import type { Clock } from './types.ts';

export interface RateLimitDecision {
  allowed: boolean;
  /** Milliseconds until at least one token is available (0 when denied by strikes). */
  retryAfterMs: number;
}

interface Bucket {
  tokens: number;
  lastRefillMs: number;
}

export interface WsRateLimiterOptions {
  /** Tokens available at full burst (per-minute budget). */
  capacity: number;
  /** Tokens added per minute, applied continuously (per second = rate/60). */
  perMinute: number;
  /** Consecutive denials tolerated before the connection must be closed. */
  maxStrikes: number;
  clock?: Clock;
}

/**
 * Per-connection or per-user token bucket with strike accounting.
 * One instance per scope; not shared across connections.
 */
export class WsRateLimiter {
  private readonly buckets = new Map<string, Bucket>();
  private readonly strikes = new Map<string, { count: number; lastMs: number }>();
  private readonly capacity: number;
  private readonly perMinute: number;
  private readonly maxStrikes: number;
  private readonly clock: Clock;

  constructor(options: WsRateLimiterOptions) {
    if (options.capacity <= 0 || options.perMinute <= 0) {
      throw new Error('WsRateLimiter requires positive capacity and perMinute');
    }
    this.capacity = options.capacity;
    this.perMinute = options.perMinute;
    this.maxStrikes = options.maxStrikes;
    this.clock = options.clock ?? Date.now;
  }

  /**
   * Attempt to consume one token for `key`.
   * @returns Decision; `retryAfterMs` is the wait until the next token
   */
  tryConsume(key: string): RateLimitDecision {
    const now = this.clock();
    let bucket = this.buckets.get(key);
    if (!bucket) {
      bucket = { tokens: this.capacity, lastRefillMs: now };
      this.buckets.set(key, bucket);
    } else {
      const elapsedMs = Math.max(0, now - bucket.lastRefillMs);
      if (elapsedMs > 0) {
        bucket.tokens = Math.min(
          this.capacity,
          bucket.tokens + (elapsedMs / 60000) * this.perMinute,
        );
        bucket.lastRefillMs = now;
      }
    }
    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return { allowed: true, retryAfterMs: 0 };
    }
    const deficit = 1 - bucket.tokens;
    const retryAfterMs = Math.max(1, Math.ceil((deficit / this.perMinute) * 60000));
    const current = this.strikes.get(key);
    if (current) {
      current.count += 1;
      current.lastMs = now;
    } else {
      this.strikes.set(key, { count: 1, lastMs: now });
    }
    return { allowed: false, retryAfterMs };
  }

  /**
   * Strike count for a key.
   * @returns Strikes; the connection must close when this reaches maxStrikes
   */
  strikesFor(key: string): number {
    return this.strikes.get(key)?.count ?? 0;
  }

  /** True when the key has exhausted its strike allowance. */
  isExhausted(key: string): boolean {
    return this.strikesFor(key) >= this.maxStrikes;
  }

  /** Forget a key (connection closed or session ended). */
  forget(key: string): void {
    this.buckets.delete(key);
    this.strikes.delete(key);
  }

  /**
   * Drop buckets and strike counters whose key has been idle for `idleMs`.
   * A bucket that has fully refilled for longer than idleMs is expendable.
   */
  sweep(nowMs?: number): number {
    const now = nowMs ?? this.clock();
    const idleMs = Math.ceil((this.capacity / this.perMinute) * 60000) + 1000;
    let removed = 0;
    for (const [key, bucket] of Array.from(this.buckets.entries())) {
      if (now - bucket.lastRefillMs > idleMs) {
        this.buckets.delete(key);
        removed += 1;
      }
    }
    for (const [key, strike] of Array.from(this.strikes.entries())) {
      if (now - strike.lastMs > idleMs) {
        this.strikes.delete(key);
        removed += 1;
      }
    }
    return removed;
  }

  /** Introspection for tests. */
  size(): { buckets: number; strikes: number } {
    return { buckets: this.buckets.size, strikes: this.strikes.size };
  }
}
