import React, { Suspense, useEffect, useRef, useState } from "react";
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
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";

import { AppHeader, NavigationDrawer } from "../components";
import AuroraBackground from "../components/common/AuroraBackground";
import Overview from "../pages/Overview.jsx";
import { DataLoader } from "../services";
import { useThemeContext } from "../theme/ThemeContext";
import { ZoomProvider, useZoom } from "../hooks/useZoom.jsx";
import useTaskEvents from "../hooks/useTaskEvents.js";
import * as Sentry from "@sentry/react";
import { logInfo, logWarn } from "../services/sentryLogger.js";

const SentryRoutes = Sentry.withSentryReactRouterV7Routing(Routes);
const LazyShoppingPage = React.lazy(() => import("../pages/Shopping.jsx"));
const LazyAccountPage = React.lazy(() => import("../pages/AccountPage.jsx"));
const LazySettingsPage = React.lazy(() => import("../pages/SettingsPage.jsx"));
const LazyToolsPage = React.lazy(() => import("../pages/ToolsPage.jsx"));

// Route order determines slide direction for page transitions
const ROUTE_ORDER = ["/", "/shopping", "/account", "/settings", "/tools"];

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

function RouteTransition({ children, direction, fillHeight = false }) {
  return (
    <motion.div
      variants={directionalPageVariants}
      custom={direction}
      initial="initial"
      animate="animate"
      exit="exit"
      style={
        fillHeight
          ? {
              height: "100%",
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
            }
          : undefined
      }
    >
      {children}
    </motion.div>
  );
}

function StartupStatus({ isLoading, error }) {
  const { themeColors } = useThemeContext();
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
      <CircularProgress
        size={32}
        sx={{
          filter: `drop-shadow(0 0 8px ${themeColors.glow}60)`,
        }}
      />
      <Typography variant="h6">{message}</Typography>
      <Typography variant="body2" color="text.secondary">
        {detail}
      </Typography>
    </Box>
  );
}

function RouteFallback() {
  const { themeColors } = useThemeContext();

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
      <CircularProgress
        size={28}
        sx={{
          filter: `drop-shadow(0 0 8px ${themeColors.glow}60)`,
        }}
      />
      <Typography variant="body2" color="text.secondary">
        Loading page...
      </Typography>
    </Box>
  );
}

function DeferredRoute({ children, direction, fillHeight = false }) {
  return (
    <RouteTransition direction={direction} fillHeight={fillHeight}>
      <Suspense fallback={<RouteFallback />}>{children}</Suspense>
    </RouteTransition>
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
            <RouteTransition direction={direction}>
              <Overview />
            </RouteTransition>
          }
        />
        <Route
          path="/shopping"
          element={
            <DeferredRoute direction={direction}>
              <LazyShoppingPage />
            </DeferredRoute>
          }
        />
        <Route
          path="/account"
          element={
            <DeferredRoute direction={direction}>
              <LazyAccountPage />
            </DeferredRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <DeferredRoute direction={direction}>
              <LazySettingsPage />
            </DeferredRoute>
          }
        />
        <Route
          path="/tools"
          element={
            <DeferredRoute direction={direction} fillHeight>
              <LazyToolsPage />
            </DeferredRoute>
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
  const { useBackendHealth } = DataLoader();
  const { zoomLevel } = useZoom();
  const muiTheme = useTheme();
  const isMobile = useMediaQuery(muiTheme.breakpoints.down("md"));
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const {
    data: healthData,
    error: backendHealthError,
    isLoading: isBackendHealthLoading,
    isFetching: isBackendHealthFetching,
  } = useBackendHealth();
  const isBackendReady = healthData?.ready === true;
  const scaledViewportHeight = `calc(100dvh / ${zoomLevel})`;

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

  return (
    <>
      <AuroraBackground />
      <Box
        className="flex"
        sx={{
          width: "100%",
          height: scaledViewportHeight,
          overflow: "hidden",
          background: "transparent",
          position: "relative",
          zIndex: 1,
          zoom: zoomLevel,
        }}
      >
        <CssBaseline />
        <AppHeader
          isMobile={isMobile}
          onMenuClick={() => setMobileDrawerOpen(true)}
        />
        <NavigationDrawer
          isMobile={isMobile}
          open={mobileDrawerOpen}
          onClose={() => setMobileDrawerOpen(false)}
        />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            minWidth: 0,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            p: { xs: 2, sm: 3, md: 4, lg: 6 },
            overflowY: "auto",
            overflowX: "hidden",
          }}
        >
          <Toolbar />
          <Box
            sx={{
              flex: 1,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
            }}
          >
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
      </Box>
    </>
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
