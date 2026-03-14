import React, { memo, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
} from "@mui/material";
import { motion } from "framer-motion";
import DashboardIcon from "@mui/icons-material/Dashboard";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import ArticleIcon from "@mui/icons-material/Article";
import SettingsIcon from "@mui/icons-material/Settings";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import RedeemIcon from "@mui/icons-material/Redeem";
import { IconDatabaseExport, IconLogin2 } from "@tabler/icons-react";
import { COMMON_COLORS } from "../../theme/colors";
import { TRANSITIONS } from "../../theme/styles";
import { useThemeContext } from "../../theme/ThemeContext";
import { DRAWER_WIDTH } from "../../config";

/**
 * Navigation tabs configuration
 */
const tabs = [
  { label: "Overview", icon: <DashboardIcon />, path: "/" },
  { label: "Shopping", icon: <ShoppingCartIcon />, path: "/shopping" },
  { label: "Redeem", icon: <RedeemIcon />, path: "/redeem" },
  { label: "Account", icon: <AccountCircleIcon />, path: "/account" },
  { label: "Manual Login", icon: <IconLogin2 />, path: "/manual" },
  { label: "Logs", icon: <ArticleIcon />, path: "/logs" },
  { label: "Backup", icon: <IconDatabaseExport />, path: "/backup" },
  { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
];

/**
 * Animation variants for list items
 */
const listItemVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1],
    },
  }),
  hover: {
    scale: 1.02,
    transition: {
      duration: 0.2,
      ease: "easeOut",
    },
  },
  tap: {
    scale: 0.98,
  },
};

/**
 * NavigationDrawer Component
 *
 * Side navigation drawer with route links.
 * Highlights the active route and provides smooth navigation.
 */
const NavigationDrawer = memo(function NavigationDrawer() {
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
        [`& .MuiDrawer-paper`]: {
          width: DRAWER_WIDTH,
          boxSizing: "border-box",
        },
      }}
    >
      <Toolbar />
      <Box className="overflow-auto">
        <List sx={{ px: 1 }} role="navigation" aria-label="Main navigation">
          {tabs.map((tab, index) => (
            <motion.div
              key={tab.label}
              custom={index}
              variants={listItemVariants}
              initial="hidden"
              animate="visible"
              whileHover="hover"
              whileTap="tap"
            >
              <ListItemButton
                onClick={() => navigate(tab.path)}
                aria-label={`Navigate to ${tab.label}`}
                aria-current={isActive(tab.path) ? "page" : undefined}
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
              </ListItemButton>
            </motion.div>
          ))}
        </List>
      </Box>
    </Drawer>
  );
});

export default NavigationDrawer;
