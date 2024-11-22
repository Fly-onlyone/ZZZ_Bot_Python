import React from "react";
import ReactDOM from "react-dom";
import "./index.css";
import PermanentDrawer from "./PermanentDrawer";
import { createTheme, ThemeProvider, useMediaQuery } from "@mui/material";


function App() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");

  // Create the theme based on the user's system preference
  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? "dark" : "light"
        }
      }),
    [prefersDarkMode]
  );

  return (
    <ThemeProvider theme={theme}>
      <PermanentDrawer />
    </ThemeProvider>
  );
}

// Render the App component
ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById("root")
);