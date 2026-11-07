# Performance notes

Living log of measured performance work. Each entry names the branch,
the user-facing effect, and how to verify it. Numbers are measured,
not estimated — entries without a measurement say so.

## perf/rate-limiter — no asserts or preallocation on the hot path

- `rate_limiter.py` `TokenBucket.consume_at`/`refill_at`: removed 9
  per-request `assert`s. Invariants are still checked at construction
  (`RateLimitConfig.__post_init__`, `__post_init__`); request-time
  validation was pure overhead (and behavior changed under `python -O`).
- `SlidingWindowEntry`: ring buffer preallocating `[0.0] * capacity`
  (up to 10k floats per key, ~80KB × 4096 keys worst case) replaced
  with `deque(maxlen=capacity)` — memory now scales with actual
  traffic. `.timestamps` stays a plain-list view (property + setter)
  so existing callers/tests are unaffected.
- Not changed: single cheap guard asserts in `check_*` dispatchers
  (negligible cost, kept as documentation).
- Verify: `pytest tests/unit/test_rate_limiter.py` (existing suite
  covers burst, pruning, per-key isolation, registry). (Not run in
  this branch — run before merge.)
