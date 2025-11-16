import React, { memo, useEffect, useMemo } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import SettingsIcon from "@mui/icons-material/Settings";
import PersonIcon from "@mui/icons-material/Person";
import PasswordIcon from "@mui/icons-material/Password";
import AppRegistrationIcon from "@mui/icons-material/AppRegistration";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import TaskIcon from "@mui/icons-material/Task";
import RedeemIcon from "@mui/icons-material/Redeem";
import { IconCards, IconLogin2 } from "@tabler/icons-react";
import zIndex from "@mui/material/styles/zIndex";

import ValueAdapter from "./ValueAdapter";
import Overview from "./Overview";
import Shopping from "./Shopping";
import ManualLogin from "./ManualLogin";
import Redeem from "./Redeem";
import { BACKEND_URL, DataLoader } from "./DataLoader";
import { COMMON_COLORS } from "./theme/colors";
import { TRANSITIONS } from "./theme/styles";
import { useThemeContext } from "./theme/ThemeContext";
import PaletteIcon from "@mui/icons-material/Palette";

const drawerWidth = 240;

const tabs = [
  { label: "Overview", icon: <DashboardIcon />, path: "/" },
  { label: "Shopping", icon: <ShoppingCartIcon />, path: "/shopping" },
  {
    label: "Redeem",
    icon: <RedeemIcon />,
    path: "/redeem",
  },
  {
    label: "Account",
    icon: <AccountCircleIcon />,
    path: "/account",
  },
  {
    label: "Manual Login",
    icon: <IconLogin2 />,
    path: "/manual",
  },
  { label: "Setting", icon: <SettingsIcon />, path: "/settings" },
];

const DrawerNavigation = memo(function DrawerNavigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const { themeColors } = useThemeContext();

  const isActive = (path) => location.pathname === path;

  // Memoize style functions to prevent recreating objects on every render
  const getListItemStyles = useMemo(
    () => (path) => ({
      borderRadius: "12px",
      mb: 0.5,
      position: "relative",
      overflow: "hidden",
      background: isActive(path)
        ? themeColors.gradients.backgroundSubtle
        : "transparent",
      borderLeft: isActive(path)
        ? `3px solid ${themeColors.secondary.main}`
        : "3px solid transparent",
      transition: TRANSITIONS.cubic,
      "&:hover": {
        background: isActive(path)
          ? themeColors.gradients.backgroundSubtle
          : `linear-gradient(135deg, ${themeColors.alpha.card} 0%, ${themeColors.alpha.card} 100%)`,
        transform: "translateX(4px)",
        borderLeft: `3px solid ${themeColors.secondary.light}`,
      },
      "&::before": {
        content: '""',
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: isActive(path)
          ? `radial-gradient(circle at top left, ${themeColors.alpha.hover}, transparent)`
          : "transparent",
        transition: TRANSITIONS.default,
      },
    }),
    [location.pathname, themeColors]
  );

  const getIconStyles = useMemo(
    () => (path) => ({
      color: isActive(path)
        ? themeColors.secondary.light
        : COMMON_COLORS.text.muted,
      minWidth: "40px",
      transition: TRANSITIONS.default,
      transform: isActive(path) ? "scale(1.1)" : "scale(1)",
    }),
    [location.pathname, themeColors]
  );

  const getTextStyles = useMemo(
    () => (path) => ({
      "& .MuiTypography-root": {
        fontWeight: isActive(path) ? 600 : 500,
        color: isActive(path)
          ? COMMON_COLORS.text.secondary
          : COMMON_COLORS.text.tertiary,
        transition: TRANSITIONS.default,
      },
    }),
    [location.pathname]
  );

  return (
    <Drawer
      className="w-60 shrink-0"
      variant="permanent"
      sx={{
        [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: "border-box" },
      }}
    >
      <Toolbar />
      <Box className="overflow-auto">
        <List sx={{ px: 1 }}>
          {tabs.map((tab) => (
            <ListItem
              button
              key={tab.label}
              onClick={() => navigate(tab.path)}
              sx={getListItemStyles(tab.path)}
            >
              <ListItemIcon sx={getIconStyles(tab.path)}>
                {tab.icon}
              </ListItemIcon>
              <ListItemText
                primary={tab.label}
                sx={getTextStyles(tab.path)}
                className="overflow-hidden text-ellipsis whitespace-nowrap"
              />
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
});

export default function PermanentDrawer() {
  const { prefetchAllRoutes } = DataLoader();
  const { themeColors } = useThemeContext();

  useEffect(() => {
    prefetchAllRoutes(); // Prefetch routes on load
  }, [prefetchAllRoutes]);
  const Qingyi02 = `${BACKEND_URL}/images/Qingyi02.ico`;
  return (
    <BrowserRouter>
      <Box className="flex bg-fixed">
        <CssBaseline />
        <AppBar position="fixed" sx={{ zIndex: zIndex.drawer + 1 }}>
          <Toolbar className="relative flex items-center justify-center">
            {/* App Icon */}
            <div className="absolute left-4 flex items-center gap-2">
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: "12px",
                  padding: "4px",
                  background: themeColors.gradients.header,
                  border: `1px solid ${themeColors.alpha.cardBorder}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: TRANSITIONS.default,
                  "&:hover": {
                    transform: "scale(1.05)",
                    boxShadow: `0 4px 20px ${themeColors.alpha.hover}`,
                  },
                }}
              >
                <img src={Qingyi02} alt="ZZZ Bot Icon" className="h-10 w-10" />
              </Box>
            </div>

            {/* App Title */}
            <Typography
              variant="h6"
              noWrap
              component="div"
              sx={{
                fontWeight: 700,
                color: COMMON_COLORS.text.primary,
                letterSpacing: "0.5px",
              }}
            >
              ZZZ Bot
            </Typography>
          </Toolbar>
        </AppBar>
        <DrawerNavigation />
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
                        "redeem_after_gather_data",
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
