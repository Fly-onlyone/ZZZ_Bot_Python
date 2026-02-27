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
import AppRegistrationIcon from "@mui/icons-material/AppRegistration";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import TaskIcon from "@mui/icons-material/Task";
import PaletteIcon from "@mui/icons-material/Palette";
import { IconCards } from "@tabler/icons-react";

import { enable, disable, isEnabled } from "@tauri-apps/plugin-autostart";
import { AppHeader, NavigationDrawer, ValueAdapter } from "../components";
import { Logs, ManualLogin, Overview, Redeem, Shopping } from "../pages";
import { DataLoader } from "../services";
import { useThemeContext } from "../theme/ThemeContext";

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
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    isEnabled()
      .then(setEnabled)
      .catch(() => {}); // Not available outside Tauri context
  }, []);

  const handleChange = async (event) => {
    const checked = event.target.checked;
    try {
      if (checked) {
        await enable();
      } else {
        await disable();
      }
      setEnabled(checked);
    } catch {
      // Ignore — running in browser dev mode without Tauri
    }
  };

  return (
    <Box sx={{ mt: 2, px: 1 }}>
      <FormControlLabel
        control={<Switch checked={enabled} onChange={handleChange} />}
        label="Auto-start on Login"
      />
    </Box>
  );
}

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
      <ValueAdapter
        customSections={{
          Task: {
            icon: <TaskIcon />,
            fields: [
              "schedule_times",
              "exit_after_run",
              "hide_browser",
              "run_task",
            ],
          },
          Shopping: {
            icon: <ShoppingCartIcon />,
            fields: [
              "gather_shopping_data",
              "exchange_good",
              "buy_all",
              "stop_on_failed_exchange",
              "enable_hunt_mode",
            ],
          },
          Draw: {
            icon: <IconCards />,
            fields: ["draw_item"],
          },
          Appearance: {
            icon: <PaletteIcon />,
            fields: ["theme"],
          },
          Monitoring: {
            icon: <TaskIcon />,
            fields: [
              "sentry_send_test_event",
              "sentry_traces_sample_rate",
              "sentry_profiles_sample_rate",
            ],
          },
        }}
        typeConfig={{
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
        }}
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

/**
 * Animated wrapper for route transitions
 */
function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
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
                customIcons={{
                  username: <PersonIcon className="text-blue-500" />,
                  password: <PasswordIcon className="text-red-500" />,
                  app_password: (
                    <AppRegistrationIcon className="text-red-500" />
                  ),
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
        <Route path="*" element={<Navigate to="/settings" />} />
      </Routes>
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
