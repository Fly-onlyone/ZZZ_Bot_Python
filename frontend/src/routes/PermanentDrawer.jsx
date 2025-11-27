import React, { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Box, CssBaseline, Toolbar } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import PersonIcon from "@mui/icons-material/Person";
import PasswordIcon from "@mui/icons-material/Password";
import AppRegistrationIcon from "@mui/icons-material/AppRegistration";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import TaskIcon from "@mui/icons-material/Task";
import PaletteIcon from "@mui/icons-material/Palette";
import { IconCards } from "@tabler/icons-react";

import { AppHeader, NavigationDrawer, ValueAdapter } from "../components";
import { ManualLogin, Overview, Redeem, Shopping } from "../pages";
import { DataLoader } from "../services";

/**
 * Page transition animation variants
 */
const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1],
    },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

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
          path="/settings"
          element={
            <motion.div
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
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
                }}
                typeConfig={{
                  theme: {
                    type: "select",
                    options: [
                      { value: "purple", label: "Purple" },
                      { value: "green", label: "Green" },
                      { value: "blue", label: "Blue" },
                    ],
                  },
                }}
              />
            </motion.div>
          }
        />
        <Route path="*" element={<Navigate to="/settings" />} />
      </Routes>
    </AnimatePresence>
  );
}

/**
 * PermanentDrawer Component
 *
 * Main application layout with persistent navigation drawer and header.
 * Manages routing and data prefetching.
 */
export default function PermanentDrawer() {
  const { prefetchAllRoutes } = DataLoader();

  useEffect(() => {
    prefetchAllRoutes(); // Prefetch routes on load
  }, [prefetchAllRoutes]);

  return (
    <BrowserRouter>
      <Box className="flex bg-fixed">
        <CssBaseline />
        <AppHeader />
        <NavigationDrawer />
        <Box component="main" className="flex-grow p-6">
          <Toolbar />
          <AnimatedRoutes />
        </Box>
      </Box>
    </BrowserRouter>
  );
}
