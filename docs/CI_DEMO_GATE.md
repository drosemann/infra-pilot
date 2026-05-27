# ci and local gating demo

this document describes how seed demo gating works, how to enable/disable it per environment, and how to verify it in ci as well as locally.

overview
- demo feature flag: `VITE_DEMO_FEATURE_ENABLED` controls whether the seed demo feature is visible in the ui and whether the api seed/guard behavior is enabled.
- global status badge: a small demo flag badge is rendered in the header across the app to show if the demo flag is on or off.
- ci tests: playwright tests verify the gating by hitting an endpoint that reports the flag value and by validating ui gating behavior when the backend is reachable.

per-environment configuration
- development: set `VITE_DEMO_FEATURE_ENABLED=true` (seed demo flows available)
- staging/qa: set `VITE_DEMO_FEATURE_ENABLED=true` for tester access or false to hide
- production: set `VITE_DEMO_FEATURE_ENABLED=false` (default) to guard against accidental seeds

testing in ci
- the workflow runs two playwright test jobs:
  - demo enabled (`VITE_DEMO_FEATURE_ENABLED=true`)
  - demo disabled (`VITE_DEMO_FEATURE_ENABLED=false`)
- a dedicated playwright test file (`demo_gate.spec.ts`) verifies that the backend flag aligns with the environment value by calling `/api/demo/flag`.
- if the backend is not up in ci, the test will skip gracefully.

locally validating gating (one-off)
- start the app with flag on:
  - unix/macos: export `VITE_DEMO_FEATURE_ENABLED=true`; (cd services/management-panel; npm ci; npm run dev)
  - windows powershell: `$env:VITE_DEMO_FEATURE_ENABLED = "true"`; cd services\management-panel; npm ci; npm run dev
- open app and verify seed demo button visibility and the global demo badge show on.
- start the app with flag off:
  - unix/macos: export `VITE_DEMO_FEATURE_ENABLED=false`; (cd services/management-panel; npm ci; npm run dev)
  - windows powershell: `$env:VITE_DEMO_FEATURE_ENABLED = "false"`; cd services\management-panel; npm ci; npm run dev
- run ui tests:
  - cd services/management-panel
  - `npm run test:playwright`

ui endpoints and api checks
- backend flag endpoint: get /api/demo/flag returns `{ enabled: true|false }`
- seed demo endpoint: post /api/seed-demo (requires business mode)

notes
- the flag is frontend-visible as a status badge and gating on the seed demo control; the backend endpoint ensures the gating is verifiable in ci.
- if you make further changes to gating in the repo, update this document accordingly.
