import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import PermanentDrawer from "./PermanentDrawer";
import { createTheme, ThemeProvider, useMediaQuery } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";

function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");

  // Create the theme based on the user's system preference
  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? "dark" : "light",
          primary: {
            main: "#6366f1", // Indigo
            light: "#818cf8",
            dark: "#4f46e5",
          },
          secondary: {
            main: "#8b5cf6", // Purple
            light: "#a78bfa",
            dark: "#7c3aed",
          },
          success: {
            main: "#10b981", // Emerald
            light: "#34d399",
            dark: "#059669",
          },
          error: {
            main: "#ef4444", // Red
            light: "#f87171",
            dark: "#dc2626",
          },
          warning: {
            main: "#f59e0b", // Amber
            light: "#fbbf24",
            dark: "#d97706",
          },
          info: {
            main: "#06b6d4", // Cyan
            light: "#22d3ee",
            dark: "#0891b2",
          },
          background: {
            default: prefersDarkMode ? "#0f172a" : "#f8fafc",
            paper: prefersDarkMode ? "#1e293b" : "#ffffff",
          },
        },
        components: {
          MuiOutlinedInput: {
            styleOverrides: {
              root: {
                transition: "all 0.3s ease-in-out",
                "& .MuiOutlinedInput-notchedOutline": {
                  borderColor: "#6366f1",
                  borderWidth: 2,
                  transition: "all 0.3s ease-in-out",
                },
                "&:hover .MuiOutlinedInput-notchedOutline": {
                  borderColor: "#8b5cf6",
                  boxShadow: "0 0 10px rgba(139, 92, 246, 0.3)",
                },
                "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                  borderColor: "#a78bfa",
                  borderWidth: 2,
                  boxShadow: "0 0 15px rgba(167, 139, 250, 0.4)",
                },
              },
            },
          },
          MuiInputLabel: {
            styleOverrides: {
              root: {
                color: "#94a3b8",
                transition: "all 0.3s ease-in-out",
                "&.Mui-focused": {
                  color: "#a78bfa",
                },
              },
            },
          },
          MuiInputBase: {
            styleOverrides: {
              root: {
                color: "#e2e8f0",
                transition: "all 0.3s ease-in-out",
              },
            },
          },
          MuiSvgIcon: {
            styleOverrides: {
              root: {
                transition: "all 0.3s ease-in-out",
              },
            },
          },
          MuiDrawer: {
            styleOverrides: {
              paper: {
                background: prefersDarkMode
                  ? "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)"
                  : "#ffffff",
                borderRadius: "0 16px 16px 0",
                border: "none",
                borderRight: `1px solid ${
                  prefersDarkMode ? "#334155" : "#e2e8f0"
                }`,
                boxShadow: "4px 0 24px rgba(0, 0, 0, 0.15)",
                transition: "all 0.3s ease-in-out",
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                background: prefersDarkMode
                  ? "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
                  : "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                backdropFilter: "blur(10px)",
                boxShadow: "0 4px 20px rgba(0, 0, 0, 0.2)",
                borderBottom: `1px solid ${
                  prefersDarkMode ? "#334155" : "rgba(255,255,255,0.1)"
                }`,
                transition: "all 0.3s ease-in-out",
              },
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                borderRadius: "8px",
                textTransform: "none",
                fontWeight: 600,
                transition: "all 0.3s ease-in-out",
                "&:hover": {
                  transform: "translateY(-2px)",
                  boxShadow: "0 6px 20px rgba(139, 92, 246, 0.4)",
                },
              },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                backgroundImage: "none",
                transition: "all 0.3s ease-in-out",
              },
            },
          },
          MuiListItem: {
            styleOverrides: {
              root: {
                transition: "all 0.3s ease-in-out",
                borderRadius: "8px",
                margin: "4px 8px",
              },
            },
          },
        },
        typography: {
          fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
          h5: {
            fontWeight: 700,
            letterSpacing: "-0.02em",
          },
          h6: {
            fontWeight: 600,
            letterSpacing: "-0.01em",
          },
        },
      }),
    [prefersDarkMode]
  );
  const queryClient = new QueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <ThemeProvider theme={theme}>
          <PermanentDrawer />
        </ThemeProvider>
      </LocalizationProvider>
    </QueryClientProvider>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
