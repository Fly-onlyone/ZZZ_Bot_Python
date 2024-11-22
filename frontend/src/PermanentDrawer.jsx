import React from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  AppBar, Box, CssBaseline, Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, Typography
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";
import SettingsIcon from "@mui/icons-material/Settings";
import Setting from "./Setting";

const drawerWidth = 240;
const BACKEND_URL = "http://127.0.0.1:8000"; // Base backend URL

const tabs = [{ label: "Overview", icon: <DashboardIcon />, path: "/" }, {
  label: "Account", icon: <AccountCircleIcon />, path: "/account"
}, { label: "Setting", icon: <SettingsIcon />, path: "/settings" }];

function DrawerNavigation() {
  const navigate = useNavigate();

  return (<Drawer
    variant="permanent"
    sx={{
      width: drawerWidth, flexShrink: 0, [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: "border-box" }
    }}
  >
    <Box sx={{ overflow: "auto" }}>
      <List>
        {tabs.map((tab) => (<ListItem
          button
          key={tab.label}
          onClick={() => navigate(tab.path)} // Use relative path
        >
          <ListItemIcon>{tab.icon}</ListItemIcon>
          <ListItemText primary={tab.label} />
        </ListItem>))}
      </List>
    </Box>
  </Drawer>);
}

export default function PermanentDrawer() {
  return (<BrowserRouter basename={BACKEND_URL.replace("http://127.0.0.1:8000", "")}>
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      {/* AppBar/Header */}
      <AppBar
        position="fixed"
        sx={{
          width: `calc(100% - ${drawerWidth}px)`, ml: `${drawerWidth}px` // Margin to avoid overlapping with the drawer
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap>
            ZZZ Bot
          </Typography>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <DrawerNavigation />

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1, p: 3, mt: 8 // Push content down to avoid overlapping with the header
        }}
      >
        <Routes>
          <Route path="/" element={<h1>Overview Page</h1>} />
          <Route path="/account" element={<h1>Account Page</h1>} />
          <Route path="/settings" element={<Setting />} />
          <Route path="*" element={<Navigate to="/settings" />} />
        </Routes>
      </Box>
    </Box>
  </BrowserRouter>);
}