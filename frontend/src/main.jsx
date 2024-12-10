import React from "react";
import ReactDOM from "react-dom";
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
        },
        components: {
          MuiOutlinedInput: {
            styleOverrides: {
              root: {
                "& .MuiOutlinedInput-notchedOutline": {
                  borderColor: "green", // Default border color
                  borderWidth: 3,
                },
                "&:hover .MuiOutlinedInput-notchedOutline": {
                  borderColor: "orange", // Border color on hover
                },
              },
            },
          },
          MuiInputLabel: {
            styleOverrides: {
              root: {
                color: "lightgreen", // Label text color
                "&.Mui-focused": {
                  color: "orange", // Label color when focused
                },
              },
            },
          },
          MuiInputBase: {
            styleOverrides: {
              root: {
                color: "cyan",
              },
            },
          },
          MuiSvgIcon: {
            styleOverrides: {
              root: {
                color: "cyan",
              },
            },
          },
          MuiDrawer: {
            styleOverrides: {
              root: {
                "& .MuiDrawer-paper": {
                  borderRadius: "16px",
                  borderLeft: "1px solid lightgreen",
                  borderRight: "1px solid lightgreen",
                  borderTop: "1px solid lightgreen",
                  borderBottom: "1px solid lightgreen",
                },
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                borderRadius: "16px",
                borderLeft: "1px solid lightgreen",
                borderRight: "1px solid lightgreen",
                borderTop: "1px solid lightgreen",
                borderBottom: "1px solid lightgreen",
              },
            },
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
