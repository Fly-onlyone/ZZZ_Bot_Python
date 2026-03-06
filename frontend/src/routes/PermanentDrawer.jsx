import React, { useEffect, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import {
  Box,
  CircularProgress,
  CssBaseline,
  FormControlLabel,
  Switch,
  Toolbar,
  Typography,
} from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import PersonIcon from "@mui/icons-material/Person";
import PasswordIcon from "@mui/icons-material/Password";
import CampaignIcon from "@mui/icons-material/Campaign";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import TaskIcon from "@mui/icons-material/Task";
import TuneIcon from "@mui/icons-material/Tune";
import { IconCards } from "@tabler/icons-react";

import { enable, disable, isEnabled } from "@tauri-apps/plugin-autostart";
import { AppHeader, NavigationDrawer, ValueAdapter } from "../components";
import { BACKEND_URL } from "../config";
import { Logs, ManualLogin, Overview, Redeem, Shopping } from "../pages";
import { DataLoader } from "../services";
import { useThemeContext } from "../theme/ThemeContext";
import * as Sentry from "@sentry/react";

const SentryRoutes = Sentry.withSentryReactRouterV7Routing(Routes);

/**
 * Page transition animation variants
 */
const pageVariants = {
  initial: {
    opacity: 0,
    y: 10,
    scale: 0.98,
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 20,
      mass: 1,
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    scale: 0.98,
    transition: {
      duration: 0.2,
      ease: "easeInOut",
    },
  },
};

function AutostartToggle() {
  const { useRouteData } = DataLoader();
  const { data: settings = {} } = useRouteData("settings");
  const [enabled, setEnabled] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const persistedPreference = settings?.autostart_on_login;
    if (typeof persistedPreference === "boolean") {
      setEnabled(persistedPreference);
      setLoaded(true);
      return;
    }

    let isMounted = true;
    isEnabled()
      .then((value) => {
        if (!isMounted) {
          return;
        }
        setEnabled(value);
        setLoaded(true);
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }
        setLoaded(true);
      });

    return () => {
      isMounted = false;
    };
  }, [settings?.autostart_on_login]);

  const persistPreference = async (checked) => {
    const response = await fetch(`${BACKEND_URL}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ autostart_on_login: checked }),
    });

    if (!response.ok) {
      throw new Error("Failed to save auto-start preference.");
    }
  };

  const handleChange = async (event) => {
    const checked = event.target.checked;
    setSaving(true);
    try {
      if (checked) {
        await enable();
      } else {
        await disable();
      }

      try {
        await persistPreference(checked);
        setEnabled(checked);
      } catch {
        if (checked) {
          await disable().catch(() => {});
        } else {
          await enable().catch(() => {});
        }
      }
    } catch {
      // Ignore — running in browser dev mode without Tauri
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box sx={{ mt: 2, px: 1 }}>
      <FormControlLabel
        control={
          <Switch
            checked={enabled}
            disabled={!loaded || saving}
            onChange={handleChange}
          />
        }
        label="Auto-start on Login"
      />
    </Box>
  );
}

const settingsTypeConfig = {
  theme: {
    type: "select",
    options: [
      { value: "nebula", label: "Nebula" },
      { value: "venom", label: "Venom" },
      { value: "glacier", label: "Glacier" },
      { value: "cyber", label: "Cyber" },
    ],
  },
  sentry_traces_sample_rate: {
    type: "select",
    options: [
      { value: 1.0, label: "1.0 (Always)" },
      { value: 0.5, label: "0.5" },
      { value: 0.25, label: "0.25" },
      { value: 0.1, label: "0.1" },
    ],
  },
  sentry_profiles_sample_rate: {
    type: "select",
    options: [
      { value: 1.0, label: "1.0 (Always)" },
      { value: 0.5, label: "0.5" },
      { value: 0.25, label: "0.25" },
      { value: 0.1, label: "0.1" },
    ],
  },
  hunt_poll_max_wait_seconds: {
    type: "select",
    options: [
      { value: 60, label: "60s" },
      { value: 120, label: "120s" },
      { value: 180, label: "180s (Default)" },
      { value: 300, label: "300s" },
    ],
  },
  hunt_poll_interval_seconds: {
    type: "select",
    options: [
      { value: 1, label: "1s (Default)" },
      { value: 2, label: "2s" },
      { value: 3, label: "3s" },
      { value: 5, label: "5s" },
    ],
  },
};

function formatCleanupSummary(report) {
  const deleted = report?.deleted || {};
  return (
    `Cleanup completed. Deleted ` +
    `${deleted["auth_storage_file"] || 0} auth file(s), ` +
    `${deleted["log_files"] || 0} log file(s), ` +
    `${deleted["screenshot_files"] || 0} screenshot file(s), ` +
    `${deleted["json_files"] || 0} JSON file(s).`
  );
}

function StartupStatus({ isLoading, error }) {
  const message = isLoading ? "Starting backend..." : "Waiting for backend...";
  const detail = error
    ? "Connection failed during startup. Retrying automatically."
    : "Please wait while services initialize.";

  return (
    <Box
      sx={{
        minHeight: "50vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
      }}
    >
      <CircularProgress size={32} />
      <Typography variant="h6">{message}</Typography>
      <Typography variant="body2" color="text.secondary">
        {detail}
      </Typography>
    </Box>
  );
}

function SettingsPanel() {
  const { useActionData } = DataLoader();
  const cleanupMutation = useActionData("maintenance/local-cleanup");

  const handleRunCleanup = async () => {
    return cleanupMutation.mutateAsync({});
  };

  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Common automation options stay here. Advanced keeps tuning and
        monitoring controls out of the main setup.
      </Typography>
      <ValueAdapter
        customSections={{
          General: {
            icon: <TaskIcon />,
            fields: ["schedule_times", "run_task", "hide_browser", "theme"],
          },
          Tasks: {
            icon: <ShoppingCartIcon />,
            fields: [
              "gather_shopping_data",
              "exchange_good",
              "buy_all",
              "draw_item",
              "stop_on_failed_exchange",
            ],
          },
          Hunt: {
            icon: <TuneIcon />,
            fields: ["enable_hunt_mode"],
          },
        }}
        typeConfig={settingsTypeConfig}
        extraActions={[
          {
            key: "run-local-cleanup",
            label: "Run Local Cleanup",
            onClick: handleRunCleanup,
            successMessage: formatCleanupSummary,
            errorMessage: "Failed to run local cleanup.",
          },
        ]}
      />
      <AutostartToggle />
    </>
  );
}

function AdvancedSettingsPanel() {
  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Advanced keeps lower-frequency runtime, hunt tuning, and monitoring
        controls separate from the main settings page.
      </Typography>
      <ValueAdapter
        customSections={{
          Runtime: {
            icon: <TuneIcon />,
            fields: ["open_web_ui", "exit_after_run"],
          },
          "Hunt Tuning": {
            icon: <TaskIcon />,
            fields: [
              "hunt_poll_max_wait_seconds",
              "hunt_poll_interval_seconds",
              "hunt_poll_backoff_enabled",
              "hunt_early_exit_on_unavailable",
            ],
          },
          Monitoring: {
            icon: <IconCards />,
            fields: [
              "sentry_send_test_event",
              "sentry_traces_sample_rate",
              "sentry_profiles_sample_rate",
            ],
          },
        }}
        typeConfig={settingsTypeConfig}
      />
    </>
  );
}

/**
 * Animated wrapper for route transitions
 */
function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <SentryRoutes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Overview />
            </motion.div>
          }
        />
        <Route
          path="/account"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <ValueAdapter
                customSections={{
                  "HoYo Account": {
                    icon: (
                      <img
                        src={`${BACKEND_URL}/images/Hoyo.png`}
                        alt="HoYoLab"
                        style={{
                          width: "1.5rem",
                          height: "1.5rem",
                          borderRadius: "4px",
                        }}
                      />
                    ),
                    fields: ["hoyo_username", "hoyo_password"],
                  },
                  "Apprise Notification": {
                    icon: <CampaignIcon />,
                    fields: ["username", "app_password"],
                  },
                }}
                customIcons={{
                  hoyo_username: <PersonIcon />,
                  hoyo_password: <PasswordIcon />,
                  username: <PersonIcon />,
                  app_password: <PasswordIcon />,
                }}
              />
            </motion.div>
          }
        />
        <Route
          path="/shopping"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Shopping />
            </motion.div>
          }
        />
        <Route
          path="/redeem"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Redeem />
            </motion.div>
          }
        />
        <Route
          path="/manual"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <ManualLogin />
            </motion.div>
          }
        />
        <Route
          path="/logs"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Logs />
            </motion.div>
          }
        />
        <Route
          path="/settings"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <SettingsPanel />
            </motion.div>
          }
        />
        <Route
          path="/settings/advanced"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <AdvancedSettingsPanel />
            </motion.div>
          }
        />
        <Route path="*" element={<Navigate to="/settings" />} />
      </SentryRoutes>
    </AnimatePresence>
  );
}

// PermanentDrawer Component
//
// Main application layout with persistent navigation drawer and header.
// Manages routing and data prefetching.
//
export default function PermanentDrawer() {
  const { prefetchAllRoutes, useBackendHealth } = DataLoader();
  const { themeColors } = useThemeContext(); // Get theme colors
  const {
    data: healthData,
    error: backendHealthError,
    isLoading: isBackendHealthLoading,
    isFetching: isBackendHealthFetching,
  } = useBackendHealth();
  const isBackendReady = healthData?.status === "ok";

  useEffect(() => {
    if (!isBackendReady) {
      return;
    }

    void prefetchAllRoutes();
  }, [isBackendReady, prefetchAllRoutes]);

  return (
    <BrowserRouter>
      <Box
        className="flex"
        sx={{
          minHeight: "100vh",
          background: themeColors.gradients.background,
          backgroundAttachment: "fixed",
          backgroundSize: "cover",
        }}
      >
        <CssBaseline />
        <AppHeader />
        <NavigationDrawer />
        <Box component="main" className="flex-grow p-6">
          <Toolbar />
          {isBackendReady ? (
            <AnimatedRoutes />
          ) : (
            <StartupStatus
              isLoading={isBackendHealthLoading || isBackendHealthFetching}
              error={backendHealthError}
            />
          )}
        </Box>
      </Box>
    </BrowserRouter>
  );
}
