// Theme configurations for the application
// Supports multiple color schemes: purple (default), green, blue

export const THEME_COLORS = {
  nebula: {
    // Previously Purple
    primary: {
      main: "#8b5cf6", // Violet
      light: "#a78bfa",
      dark: "#7c3aed",
    },
    secondary: {
      main: "#d946ef", // Fuchsia
      light: "#e879f9",
      dark: "#c026d3",
    },
    gradients: {
      primary: "linear-gradient(135deg, #7c3aed 0%, #d946ef 100%)",
      primaryLight: "linear-gradient(135deg, #8b5cf6 0%, #e879f9 100%)",
      header:
        "linear-gradient(135deg, rgba(124, 58, 237, 0.25) 0%, rgba(217, 70, 239, 0.25) 100%)", // Increased opacity
      background: "linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%)", // Slightly lighter start
      backgroundSubtle:
        "linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(217, 70, 239, 0.1) 100%)", // Increased opacity
    },
    alpha: {
      card: "rgba(139, 92, 246, 0.12)", // Increased
      cardBorder: "rgba(139, 92, 246, 0.4)",
      hover: "rgba(139, 92, 246, 0.2)",
      divider: "rgba(139, 92, 246, 0.3)",
    },
  },
  venom: {
    // Previously Green
    primary: {
      main: "#10b981", // Emerald
      light: "#34d399",
      dark: "#059669",
    },
    secondary: {
      main: "#84cc16", // Lime
      light: "#a3e635",
      dark: "#65a30d",
    },
    gradients: {
      primary: "linear-gradient(135deg, #059669 0%, #84cc16 100%)",
      primaryLight: "linear-gradient(135deg, #34d399 0%, #a3e635 100%)",
      header:
        "linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(132, 204, 22, 0.2) 100%)", // Reduced opacity for balance
      background: "linear-gradient(180deg, #022c22 0%, #0f172a 100%)", // Deep pine (darker) to slate
      backgroundSubtle:
        "linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(132, 204, 22, 0.05) 100%)", // Reduced opacity
    },
    alpha: {
      card: "rgba(16, 185, 129, 0.12)", // Increased
      cardBorder: "rgba(16, 185, 129, 0.4)",
      hover: "rgba(16, 185, 129, 0.2)",
      divider: "rgba(16, 185, 129, 0.3)",
    },
  },
  glacier: {
    // Previously Blue
    primary: {
      main: "#0ea5e9", // Sky
      light: "#38bdf8",
      dark: "#0284c7",
    },
    secondary: {
      main: "#6366f1", // Indigo
      light: "#818cf8",
      dark: "#4f46e5",
    },
    gradients: {
      primary: "linear-gradient(135deg, #0284c7 0%, #6366f1 100%)",
      primaryLight: "linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)",
      header:
        "linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%)", // Increased opacity
      background: "linear-gradient(180deg, #172554 0%, #0f172a 100%)", // Slightly lighter start
      backgroundSubtle:
        "linear-gradient(135deg, rgba(14, 165, 233, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%)", // Increased opacity
    },
    alpha: {
      card: "rgba(14, 165, 233, 0.12)", // Increased
      cardBorder: "rgba(14, 165, 233, 0.4)",
      hover: "rgba(14, 165, 233, 0.2)",
      divider: "rgba(14, 165, 233, 0.3)",
    },
  },
  cyber: {
    primary: {
      main: "#d946ef", // Fuschia
      light: "#f0abfc",
      dark: "#a21caf",
    },
    secondary: {
      main: "#06b6d4", // Cyan
      light: "#67e8f9",
      dark: "#0891b2",
    },
    gradients: {
      primary: "linear-gradient(135deg, #d946ef 0%, #06b6d4 100%)",
      primaryLight: "linear-gradient(135deg, #f0abfc 0%, #67e8f9 100%)",
      header:
        "linear-gradient(135deg, rgba(217, 70, 239, 0.25) 0%, rgba(6, 182, 212, 0.25) 100%)", // Increased opacity
      background: "linear-gradient(180deg, #2e1065 0%, #0f172a 100%)", // Slightly lighter start
      backgroundSubtle:
        "linear-gradient(135deg, rgba(217, 70, 239, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%)", // Increased opacity
    },
    alpha: {
      card: "rgba(217, 70, 239, 0.12)",
      cardBorder: "rgba(217, 70, 239, 0.4)",
      hover: "rgba(217, 70, 239, 0.2)",
      divider: "rgba(217, 70, 239, 0.3)",
    },
  },
};

// Common colors shared across all themes
export const COMMON_COLORS = {
  success: {
    main: "#10b981",
    light: "#34d399",
    dark: "#059669",
  },
  error: {
    main: "#ef4444",
    light: "#f87171",
    dark: "#dc2626",
  },
  warning: {
    main: "#f59e0b",
    light: "#fbbf24",
    dark: "#d97706",
  },
  info: {
    main: "#06b6d4",
    light: "#22d3ee",
    dark: "#0891b2",
  },
  text: {
    primary: "#f1f5f9",
    secondary: "#e2e8f0",
    tertiary: "#cbd5e1",
    muted: "#94a3b8",
  },
  background: {
    dark: "#0f172a",
    paper: "#1e293b",
    slate: "#334155",
  },
};

/**
 * Get theme colors for a specific theme name
 * @param {string} themeName - Name of the theme (purple, green, blue)
 * @returns {object} Theme color configuration
 */
export function getThemeColors(themeName = "nebula") {
  return THEME_COLORS[themeName] || THEME_COLORS.nebula;
}

/**
 * Create MUI theme configuration for a specific color theme
 * @param {string} themeName - Name of the theme (nebula, venom, glacier, cyber)
 * @param {boolean} isDark - Whether dark mode is enabled
 * @returns {object} MUI theme palette configuration
 */
export function createThemePalette(themeName = "nebula", isDark = true) {
  const themeColors = getThemeColors(themeName);

  return {
    mode: isDark ? "dark" : "light",
    primary: themeColors.primary,
    secondary: themeColors.secondary,
    success: COMMON_COLORS.success,
    error: COMMON_COLORS.error,
    warning: COMMON_COLORS.warning,
    info: COMMON_COLORS.info,
    background: {
      default: isDark ? COMMON_COLORS.background.dark : "#f8fafc",
      paper: isDark ? COMMON_COLORS.background.paper : "#ffffff",
    },
  };
}
