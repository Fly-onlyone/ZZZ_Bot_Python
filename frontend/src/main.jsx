import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import PermanentDrawer from "./routes/PermanentDrawer";
import { ThemeProvider, useMediaQuery } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { ThemeContextProvider, useThemeContext } from "./theme/ThemeContext";
import { createMuiTheme } from "./theme/muiTheme";

function ThemedApp() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const { themeName, themeColors } = useThemeContext();

  // Create the theme based on the selected theme and system preference
  const theme = React.useMemo(
    () => createMuiTheme(themeName, prefersDarkMode, themeColors),
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
