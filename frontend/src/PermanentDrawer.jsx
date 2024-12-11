import React, { useEffect } from "react";
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
import ValueAdapter from "./ValueAdapter";
import zIndex from "@mui/material/styles/zIndex";
import Overview from "./Overview";
import Shopping from "./Shopping";
import TaskIcon from "@mui/icons-material/Task";
import InputIcon from "@mui/icons-material/Input";
import ManualLogin from "./ManualLogin";
import { IconCards, IconLogin2 } from "@tabler/icons-react";
import ShuffleOnIcon from "@mui/icons-material/ShuffleOn";
import { BACKEND_URL, DataLoader } from "./DataLoader";

const drawerWidth = 240;

const tabs = [
  { label: "Overview", icon: <DashboardIcon />, path: "/" },
  { label: "Shopping", icon: <ShoppingCartIcon />, path: "/shopping" },
  {
    label: "Account",
    icon: <AccountCircleIcon />,
    path: "/account",
  },
  {
    label: "Manual Login",
    icon: <IconLogin2 className="stroke-cyan-500" />,
    path: "/manual",
  },
  { label: "Setting", icon: <SettingsIcon />, path: "/settings" },
];

function DrawerNavigation() {
  const navigate = useNavigate();
  const location = useLocation();

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
  const { prefetchAllRoutes } = DataLoader();
  useEffect(() => {
    prefetchAllRoutes(); // Prefetch routes on load
  }, [prefetchAllRoutes]);
  const Qingyi02 = `${BACKEND_URL}/icon/Qingyi02.ico`;
  return (
    <BrowserRouter>
      <Box className="flex">
        <CssBaseline />
        <AppBar
          position="fixed"
          sx={{ zIndex: zIndex.drawer + 1 }}
          className="w-full bg-black"
        >
          <Toolbar className="relative flex items-center justify-center">
            {/* Icon on the Left */}
            <div className="absolute left-4 flex items-center">
              <img src={Qingyi02} alt="ZZZ Bot Icon" className="h-12 w-12" />
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
                        "headless_mode",
                        "run_task",
                      ],
                    },
                    Shopping: {
                      icon: <ShoppingCartIcon />,
                      fields: [
                        "gather_shopping_data",
                        "redeem_after_gather_data",
                        "buy_all",
                      ],
                    },
                    Draw: {
                      icon: <IconCards className=" stroke-cyan-500" />,
                      fields: ["draw_item"],
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
