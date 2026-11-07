# Performance notes

Living log of measured performance work. Each entry names the branch,
the user-facing effect, and how to verify it. Numbers are measured,
not estimated — entries without a measurement say so.

## perf/frontend-polling — one shared GET cache instead of 14 pollers

- `src/lib/api.ts`: all polling components go through `APIClient`,
  so the fix lives there, not in 14 components. Axios GET is wrapped
  once: concurrent identical requests share one in-flight promise,
  responses are cached 5s (bounded to 200 entries), the last response
  is served without network while the tab is hidden, and any
  POST/PATCH/DELETE clears the cache (no stale reads after writes).
- Side effect that removes re-renders: cache hits return the same
  object reference, so `setState(cached)` bails out via `Object.is`.
- No automated test (needs a network stub; not added blind). Verify in
  devtools: duplicate dashboard widgets fire one request; hidden tab
  fires none. `npm run typecheck` + `npm test` before merge — not run
  in this branch.
