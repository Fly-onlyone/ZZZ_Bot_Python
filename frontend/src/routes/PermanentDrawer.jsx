import React, { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Box, CssBaseline, Toolbar } from "@mui/material";
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
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route
              path="/account"
              element={
                <ValueAdapter
                  customIcons={{
                    username: <PersonIcon className="text-blue-500" />,
                    password: <PasswordIcon className="text-red-500" />,
                    app_password: (
                      <AppRegistrationIcon className="text-red-500" />
                    ),
                  }}
                />
              }
            />
            <Route path="/shopping" element={<Shopping />} />
            <Route path="/redeem" element={<Redeem />} />
            <Route path="/manual" element={<ManualLogin />} />
            <Route
              path="/settings"
              element={
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
              }
            />
            <Route path="*" element={<Navigate to="/settings" />} />
          </Routes>
        </Box>
      </Box>
    </BrowserRouter>
  );
}
