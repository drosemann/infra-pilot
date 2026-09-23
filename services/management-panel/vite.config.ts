/**
 * @file Vite configuration for the management-panel frontend.
 * Supports both web-only mode and Tauri desktop builds.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const host = process.env.TAURI_DEV_HOST;

// Single source of truth for the displayed product version:
// explicit APP_VERSION wins, then the npm package version,
// then 'dev' for ad-hoc runs outside npm. Injected as
// __APP_VERSION__ so the UI never hardcodes a version string.
const appVersion =
  process.env.APP_VERSION || process.env.npm_package_version || "dev";

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: "ws", host, port: 5174 } : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
  envPrefix: ["VITE_", "TAURI_"],
  build: {
    target: process.env.TAURI_ENV_PLATFORM === "windows" ? "chrome105" : "safari13",
    minify: process.env.TAURI_ENV_DEBUG ? false : "oxc",
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
  },
});
