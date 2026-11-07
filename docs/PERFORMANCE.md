# Performance notes

Living log of measured performance work. Each entry names the branch,
the user-facing effect, and how to verify it. Numbers are measured,
not estimated — entries without a measurement say so.

## perf/api-payloads — bounded list endpoints via `?limit=`

- `server/index.ts`: new `boundedLimit(req, def, max)` helper; the
  polled, previously unbounded list queries now carry a default cap
  with client override: ssh_sessions (50/200), customers (200/500),
  webhooks (100/500), webhook_logs (100/500), server_inventory
  (100/500), plugins (100/500), changes/history (50/200).
- Deliberately untouched: secrets-rotation scans (`select('*')` with
  `rotate=true`) must see every due row — a limit there would skip
  rotations. Single-row `.single()` lookups need no limit.
- Verify: response byte size stays flat as tables grow
  (`?limit=` respected, clamped to max). (Not run in this branch —
  run before merge.)
