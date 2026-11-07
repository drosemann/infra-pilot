# Performance notes

Living log of measured performance work. Each entry names the branch,
the user-facing effect, and how to verify it. Numbers are measured,
not estimated — entries without a measurement say so.

## perf/ws-metrics-sampler — one docker-stats sampler per app

- `server/index.ts`: every `subscribe:metrics` WebSocket opened its own
  2s `setInterval` spawning `docker stats`. Now one 5s interval per
  appId (`metricsSubs`) samples once and broadcasts the same payload
  to all subscribers; the timer stops when the last client leaves.
- Effect: process spawns for metrics go from N_subscribers to 1 per
  app; host CPU and Docker daemon load drop proportionally.
- Verify: open 3 detail views on one app, count `docker stats`
  spawns (expect ~1 per 5s, not ~3 per 2s). (Not run in this branch —
  run before merge.)
