import React, { useEffect, useRef } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { Box, CircularProgress, CssBaseline, Toolbar, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import PersonIcon from "@mui/icons-material/Person";
import PasswordIcon from "@mui/icons-material/Password";
import CampaignIcon from "@mui/icons-material/Campaign";

import { AppHeader, NavigationDrawer, ValueAdapter } from "../components";
import { BACKEND_URL } from "../config";
import {
  Backup,
  Logs,
  ManualLogin,
  Overview,
  Redeem,
  SettingsPage,
  Shopping,
} from "../pages";
import { DataLoader } from "../services";
import { useThemeContext } from "../theme/ThemeContext";
import { ZoomProvider, useZoom } from "../hooks/useZoom.jsx";
import useTaskEvents from "../hooks/useTaskEvents.js";
import * as Sentry from "@sentry/react";
import { logInfo, logWarn } from "../services/sentryLogger.js";

const SentryRoutes = Sentry.withSentryReactRouterV7Routing(Routes);

// Route order determines slide direction for page transitions
const ROUTE_ORDER = [
  "/",
  "/shopping",
  "/redeem",
  "/account",
  "/manual",
  "/logs",
  "/backup",
  "/settings",
];

function useTransitionDirection() {
  const location = useLocation();
  const prevPathRef = useRef(location.pathname);

  useEffect(() => {
    prevPathRef.current = location.pathname;
  }, [location.pathname]);

  const prevIndex = ROUTE_ORDER.indexOf(prevPathRef.current);
  const currIndex = ROUTE_ORDER.indexOf(location.pathname);

  // Default to forward (1) if route not found in order
  if (prevIndex === -1 || currIndex === -1) return 1;
  return currIndex >= prevIndex ? 1 : -1;
}

const directionalPageVariants = {
  initial: (direction) => ({
    opacity: 0,
    x: direction * 40,
    scale: 0.98,
  }),
  animate: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 20,
      mass: 1,
    },
  },
  exit: (direction) => ({
    opacity: 0,
    x: direction * -40,
    scale: 0.98,
    transition: {
      duration: 0.2,
      ease: "easeInOut",
    },
  }),
};

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

/**
 * Animated wrapper for route transitions
 */
function AnimatedRoutes() {
  const location = useLocation();
  const direction = useTransitionDirection();

  useEffect(() => {
    logInfo("Frontend route viewed", {
      route: location.pathname,
    });
  }, [location.pathname]);

  return (
    <AnimatePresence mode="wait" custom={direction}>
      <SentryRoutes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <motion.div
              variants={directionalPageVariants}
              custom={direction}
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
              variants={directionalPageVariants}
              custom={direction}
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
              variants={directionalPageVariants}
              custom={direction}
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
              variants={directionalPageVariants}
              custom={direction}
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
              variants={directionalPageVariants}
              custom={direction}
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
              variants={directionalPageVariants}
              custom={direction}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Logs />
            </motion.div>
          }
        />
        <Route
          path="/backup"
          element={
            <motion.div
              variants={directionalPageVariants}
              custom={direction}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Backup />
            </motion.div>
          }
        />
        <Route
          path="/settings"
          element={
            <motion.div
              variants={directionalPageVariants}
              custom={direction}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <SettingsPage />
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
function PermanentDrawerContent() {
  const { prefetchAllRoutes, useBackendHealth } = DataLoader();
  const { themeColors } = useThemeContext();
  const { zoomLevel } = useZoom();
  const {
    data: healthData,
    error: backendHealthError,
    isLoading: isBackendHealthLoading,
    isFetching: isBackendHealthFetching,
  } = useBackendHealth();
  const isBackendReady = healthData?.status === "ok";

  useTaskEvents({ enabled: isBackendReady });

  useEffect(() => {
    if (!isBackendReady) {
      return;
    }

    logInfo("Frontend backend connected", {
      status: healthData?.status || "unknown",
    });
  }, [healthData?.status, isBackendReady]);

  useEffect(() => {
    if (
      !backendHealthError ||
      isBackendHealthLoading ||
      isBackendHealthFetching
    ) {
      return;
    }

    logWarn("Frontend backend health check failed", {
      error:
        backendHealthError instanceof Error
          ? backendHealthError.message
          : String(backendHealthError),
    });
  }, [backendHealthError, isBackendHealthFetching, isBackendHealthLoading]);

  useEffect(() => {
    if (!isBackendReady) {
      return;
    }

    void prefetchAllRoutes();
  }, [isBackendReady, prefetchAllRoutes]);

  return (
    <Box
      className="flex"
      sx={{
        minHeight: "100vh",
        background: themeColors.gradients.background,
        backgroundAttachment: "fixed",
        backgroundSize: "cover",
        zoom: zoomLevel,
      }}
    >
      <CssBaseline />
      <AppHeader />
      <NavigationDrawer />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, sm: 3, md: 4, lg: 6 },
          overflow: "auto",
        }}
      >
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
  );
}

export default function PermanentDrawer() {
  const containerRef = useRef(null);

  return (
    <BrowserRouter>
      <div ref={containerRef} style={{ width: "100%", height: "100%" }}>
        <ZoomProvider containerRef={containerRef}>
          <PermanentDrawerContent />
        </ZoomProvider>
      </div>
    </BrowserRouter>
  );
}
