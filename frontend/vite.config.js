import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const FRONTEND_DIR = fileURLToPath(new URL(".", import.meta.url));
const PROJECT_ROOT = resolve(FRONTEND_DIR, "..");

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const frontendEnv = loadEnv(mode, FRONTEND_DIR, "");
  const rootEnv = loadEnv(mode, PROJECT_ROOT, "");

  const frontendSentryDsn =
    process.env.VITE_SENTRY_DSN ||
    frontendEnv.VITE_SENTRY_DSN ||
    process.env.SENTRY_FRONTEND_DSN ||
    frontendEnv.SENTRY_FRONTEND_DSN ||
    rootEnv.VITE_SENTRY_DSN ||
    rootEnv.SENTRY_FRONTEND_DSN ||
    "";

  return {
    plugins: [react()],
    clearScreen: false,
    define: {
      // Keep client code on the standard VITE_ key while accepting the
      // repository root SENTRY_FRONTEND_DSN used by product builds.
      "import.meta.env.VITE_SENTRY_DSN": JSON.stringify(frontendSentryDsn),
    },
    server: {
      host: "127.0.0.1",
      port: 3000,
      strictPort: true,
    },
  };
});
