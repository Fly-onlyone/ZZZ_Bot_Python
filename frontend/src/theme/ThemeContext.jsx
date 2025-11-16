import React, { createContext, useContext, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getThemeColors } from "./themes";

const BACKEND_URL = import.meta.env.PROD
  ? "http://127.0.0.1:8000"
  : "http://127.0.0.1:8000";

const ThemeContext = createContext({
  themeName: "purple",
  themeColors: getThemeColors("purple"),
});

export function ThemeContextProvider({ children }) {
  const [themeName, setThemeName] = useState("purple");
  const [themeColors, setThemeColors] = useState(getThemeColors("purple"));

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
    const newTheme = settingsData?.theme || "purple";
    setThemeName(newTheme);
    setThemeColors(getThemeColors(newTheme));
  }, [settingsData]);

  return (
    <ThemeContext.Provider value={{ themeName, themeColors }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeContext() {
  return useContext(ThemeContext);
}
