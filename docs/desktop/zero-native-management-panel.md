# zero-native management panel shell

infra pilot now includes a zero-native desktop shell for the react/vite management panel. this is the part of the project that can be rewritten cleanly to zero-native today: the user interface runs in a native webview shell, while the express api, orchestrator, and service-core remain long-running services.

## what changed

• `services/management-panel/app.zon` is the zero-native app manifest. it defines the app identity, webview source, vite dev-server command, navigation policy, and main window size.
• `services/management-panel/native/src/main.zig` is the zig native entry point. it selects a zero-native platform backend, loads `dist/index.html` for production, and switches to the managed vite url when `zero_native_frontend_url` is set by `zero-native dev`.
• `services/management-panel/build.zig` adds desktop-oriented build steps around the existing frontend build.
• the existing express api is intentionally not embedded into zig. keep it as the local api process on `http://127.0.0.1:3001` so docker, database, and authentication integrations continue to work unchanged.

## prerequisites

• zig 0.16.0 or newer.
• node.js 18+ with npm.
• the zero-native cli: `npm install -g zero-native`.
• a zero-native framework checkout available at `vendor/zero-native` from the repository root, or pass `-dzero-native-path=/path/to/zero-native` to zig.
• linux desktop builds need gtk4 and webkitgtk 6 development packages. macos uses the system webkit runtime.

## development flow

run the api in one terminal:

```bash
cd services/management-panel
npm run dev:backend
```

run the native shell in another terminal:

```bash
cd services/management-panel
npm run desktop:dev -- -Dzero-native-path=/absolute/path/to/zero-native
```

`desktop:dev` builds the zig shell and delegates frontend lifecycle management to `zero-native dev`, which starts vite, waits for `http://127.0.0.1:5173/`, injects `zero_native_frontend_url`, and launches the native webview.

## production/package flow

```bash
cd services/management-panel
npm run build
npm run desktop:package -- -Dzero-native-path=/absolute/path/to/zero-native
```

the package step uses the built `dist/` directory and serves it through the `zero://app` origin declared in `app.zon`.

## validation

```bash
cd services/management-panel
npm run desktop:validate
npm run desktop:doctor
```

use `desktop:doctor` before packaging on a real workstation because it checks the host webview environment as well as the manifest.

## current boundaries

• the zero-native integration uses `.web_engine = "system"` by default for the smallest native shell.
• chromium/cef metadata is present in `app.zon`, but the local `build.zig` intentionally supports the system webview path first. add cef bundling only after the team decides it needs pinned chromium rendering.
• the browser version remains supported via `npm run dev` and docker compose.
