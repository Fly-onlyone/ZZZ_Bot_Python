import React from "react";
import ReactDOM from "react-dom/client";
import * as Sentry from "@sentry/react";
import {
  createRoutesFromChildren,
  matchRoutes,
  useLocation,
  useNavigationType,
} from "react-router-dom";
import "./index.css";
import PermanentDrawer from "./routes/PermanentDrawer";
import { ThemeProvider, useMediaQuery } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { ThemeContextProvider, useThemeContext } from "./theme/ThemeContext";
import { createMuiTheme } from "./theme/muiTheme";
import ErrorFallback from "./components/common/ErrorFallback";

const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
const DEFAULT_SAMPLE_RATE =
  import.meta.env.MODE === "development" ? "1.0" : "0.1";

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: import.meta.env.MODE,
    integrations: [
      Sentry.reactRouterV7BrowserTracingIntegration({
        useEffect: React.useEffect,
        useLocation,
        useNavigationType,
        createRoutesFromChildren,
        matchRoutes,
      }),
      Sentry.browserProfilingIntegration(),
      Sentry.captureConsoleIntegration({ levels: ["log", "warn", "error"] }),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: parseFloat(
      import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || DEFAULT_SAMPLE_RATE
    ),
    profilesSampleRate: parseFloat(
      import.meta.env.VITE_SENTRY_PROFILES_SAMPLE_RATE || DEFAULT_SAMPLE_RATE
    ),
    tracePropagationTargets: ["localhost", "127.0.0.1"],
    sendDefaultPii: false,
    replaysSessionSampleRate: import.meta.env.MODE === "development" ? 1.0 : 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
}

function ThemedApp() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const { themeName, themeColors } = useThemeContext();

  // Create the theme based on the selected theme and system preference
  const theme = React.useMemo(
    () => createMuiTheme(themeName, prefersDarkMode, themeColors),
    [prefersDarkMode, themeName, themeColors]
  );

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <ThemeProvider theme={theme}>
        <PermanentDrawer />
      </ThemeProvider>
    </LocalizationProvider>
  );
}

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContextProvider>
        <ThemedApp />
      </ThemeContextProvider>
    </QueryClientProvider>
  );
}

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element #root was not found");
}

const ROOT_KEY = "__ZZZ_BOT_APP_ROOT__";
const root = window[ROOT_KEY] || ReactDOM.createRoot(rootElement);
window[ROOT_KEY] = root;

root.render(
  <React.StrictMode>
    <Sentry.ErrorBoundary
      fallback={({ error, resetError }) => (
        <ErrorFallback error={error} resetError={resetError} />
      )}
    >
      <App />
    </Sentry.ErrorBoundary>
  </React.StrictMode>
);
