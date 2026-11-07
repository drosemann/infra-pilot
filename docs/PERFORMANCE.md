# Performance notes

Living log of measured performance work. Each entry names the branch,
the user-facing effect, and how to verify it. Numbers are measured,
not estimated — entries without a measurement say so.

## perf/server-subprocess — non-blocking CLI bridge, O(n) output capture

- `server/cli-bridge.ts`: `execSync` (blocks the whole Node event loop
  for up to 30s per call) replaced with async `execFile` (no shell;
  quote-aware arg split). `cli()` and the `ipilot` wrappers now
  return `Promise<CliResult>` — await them.
- `server/index.ts` `runCommand`: chunk-array capture (`join('')`)
  instead of `+=` per data event (O(n²) → O(n) on large log output);
  new optional `stdin` parameter. This also fixes config writes:
  the 3rd `content` argument was silently dropped before, so
  `docker exec ... tee` received empty stdin; dead `escapedContent`
  shell-escaping removed.
- Verify: `NODE_ENV=test node --test tests/unit/cli-bridge.test.ts`;
  concurrent-request latency (one slow `ipilot` call must not stall others).
  (Not run in this branch — run before merge.)
