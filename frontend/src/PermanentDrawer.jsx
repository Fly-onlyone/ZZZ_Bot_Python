import React from "react";
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
import Qingyi from "./../../Qingyi02.ico";
import ValueAdapter from "./ValueAdapter";

const tabs = [
  { label: "Overview", icon: <DashboardIcon />, path: "/" },
  {
    label: "Account",
    icon: <AccountCircleIcon />,
    path: "/account",
  },
  { label: "Setting", icon: <SettingsIcon />, path: "/settings" },
];

function DrawerNavigation() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Drawer
      variant="permanent"
      classes={{
        paper: "bg-black text-white w-[240px] h-[calc(100vh-4rem)] mt-16",
      }}
    >
      <Box className="overflow-auto">
        <List>
          {tabs.map((tab) => (
            <ListItem
              button
              key={tab.label}
              onClick={() => navigate(tab.path)}
              className={`rounded-lg hover:bg-green-900 ${
                location.pathname === tab.path ? "bg-cyan-900" : ""
              }`}
            >
              <ListItemIcon
                className={`text-inherit ${
                  location.pathname === tab.path ? "text-cyan-400" : ""
                }`}
              >
                {tab.icon}
              </ListItemIcon>
              <ListItemText
                primary={tab.label}
                className="overflow-hidden text-ellipsis whitespace-nowrap" // Prevents text overflow
              />
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
}

export default function PermanentDrawer() {
  return (
    <BrowserRouter>
      <Box className="flex h-screen">
        {/* Full-height layout */}
        <CssBaseline />
        {/* AppBar/Header */}
        <AppBar
          position="fixed"
          className="w-full bg-black bg-opacity-80 shadow-none"
        >
          <Toolbar className="relative flex items-center justify-center">
            {/* Icon on the Left */}
            <div className="absolute left-4 flex items-center">
              <img src={Qingyi} alt="ZZZ Bot Icon" className="h-12 w-12" />
            </div>
            <Typography
              variant="h6"
              noWrap
              component="div"
              className="font-bold text-white"
            >
              ZZZ Bot
            </Typography>
          </Toolbar>
        </AppBar>
        {/* Drawer */}
        <DrawerNavigation />
        {/* Main Content */}
        <Box
          component="main"
          className="ml-[240px] mt-[64px] flex-grow bg-black p-6" // Offset for the header and drawer
        >
          <Routes>
            <Route
              path="/"
              element={<h1 className="text-white">Overview Page</h1>}
            />
            <Route path="/account" element={<ValueAdapter />} />
            <Route path="/settings" element={<ValueAdapter />} />
            <Route path="*" element={<Navigate to="/settings" />} />
          </Routes>
        </Box>
      </Box>
    </BrowserRouter>
  );
}
