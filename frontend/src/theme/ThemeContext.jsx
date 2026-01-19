import React, { createContext, useContext, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getThemeColors } from "./themes";

const BACKEND_URL = import.meta.env.PROD
  ? "http://127.0.0.1:8000"
  : "http://127.0.0.1:8000";

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

  // Fetch theme setting from backend
  const { data: settingsData } = useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const response = await fetch(`${BACKEND_URL}/settings`);
      return response.json();
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: true,
  });

  useEffect(() => {
    const newTheme = settingsData?.theme || "nebula";
    setThemeName(newTheme);
    setThemeColors(getThemeColors(newTheme));
  }, [settingsData]);

  return (
    <ThemeContext.Provider
      value={{ themeName, themeColors, prefersReducedMotion }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeContext() {
  return useContext(ThemeContext);
}
