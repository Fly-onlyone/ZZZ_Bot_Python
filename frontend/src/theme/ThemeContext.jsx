import React, { createContext, useContext, useEffect, useState } from "react";
import { getThemeColors } from "./themes";
import { DataLoader } from "../services";

/**
 * Hook to detect user's reduced motion preference
 */
function useReducedMotionPreference() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(
    () =>
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!mediaQuery) return;

    const handleChange = (event) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return prefersReducedMotion;
}

const ThemeContext = createContext({
  themeName: "nebula",
  themeColors: getThemeColors("nebula"),
  prefersReducedMotion: false,
});

export function ThemeContextProvider({ children }) {
  const [themeName, setThemeName] = useState("nebula");
  const [themeColors, setThemeColors] = useState(getThemeColors("nebula"));
  const prefersReducedMotion = useReducedMotionPreference();

  const { useRouteData, useBackendHealth } = DataLoader();
  const { data: healthData } = useBackendHealth();
  const isBackendReady = healthData?.status === "ok";

  // Fetch theme setting from backend once health check confirms readiness.
  const { data: settingsData } = useRouteData("settings", {
    enabled: isBackendReady,
    retry: 6,
    retryDelay: (attemptIndex) => Math.min(500 * 2 ** attemptIndex, 3000),
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });

  useEffect(() => {
    const newTheme = settingsData?.theme || "nebula";
    setThemeName(newTheme);
    setThemeColors(getThemeColors(newTheme));
  }, [settingsData]);

  const changeTheme = (name) => {
    setThemeName(name);
    setThemeColors(getThemeColors(name));
  };

  return (
    <ThemeContext.Provider
      value={{ themeName, themeColors, prefersReducedMotion, changeTheme }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeContext() {
  return useContext(ThemeContext);
}
