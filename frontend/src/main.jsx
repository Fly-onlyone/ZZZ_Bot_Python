import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import PermanentDrawer from "./PermanentDrawer";
import { createTheme, ThemeProvider, useMediaQuery } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { createThemePalette } from "./theme/themes";
import { ThemeContextProvider, useThemeContext } from "./theme/ThemeContext";

function ThemedApp() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const { themeName, themeColors } = useThemeContext();

  // Create the theme based on the selected theme and system preference
  const theme = React.useMemo(
    () =>
      createTheme({
        palette: createThemePalette(themeName, prefersDarkMode),
        components: {
          MuiOutlinedInput: {
            styleOverrides: {
              root: {
                transition: "all 0.3s ease-in-out",
                "& .MuiOutlinedInput-notchedOutline": {
                  borderColor: themeColors.primary.main,
                  borderWidth: 2,
                  transition: "all 0.3s ease-in-out",
                },
                "&:hover .MuiOutlinedInput-notchedOutline": {
                  borderColor: themeColors.secondary.main,
                  boxShadow: `0 0 10px ${themeColors.alpha.hover}`,
                },
                "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                  borderColor: themeColors.secondary.light,
                  borderWidth: 2,
                  boxShadow: `0 0 15px ${themeColors.alpha.hover}`,
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
                  color: themeColors.secondary.light,
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
                  ? themeColors.gradients.background
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
                  : themeColors.gradients.primary,
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
                  boxShadow: `0 6px 20px ${themeColors.alpha.hover}`,
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
    [prefersDarkMode, themeName, themeColors]
  );

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <ThemeProvider theme={theme}>
        <PermanentDrawer />
      </ThemeProvider>
    </LocalizationProvider>
  );
}

function App() {
  const queryClient = new QueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeContextProvider>
        <ThemedApp />
      </ThemeContextProvider>
    </QueryClientProvider>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
