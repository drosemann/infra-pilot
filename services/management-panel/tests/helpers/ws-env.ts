/**
 * Side-effect module that pins gateway environment variables.
 *
 * Import this BEFORE `server/index.ts` so the values are present when the
 * module body calls `loadWsConfig(process.env)`. `??=` keeps any value the
 * operator already set.
 */
process.env.WS_AUTH_TIMEOUT_MS ??= '500';
