// Theme configurations for the application
// Supports multiple color schemes: purple (default), green, blue

export const THEME_COLORS = {
  purple: {
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
    gradients: {
      primary: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
      primaryLight: "linear-gradient(135deg, #a78bfa 0%, #818cf8 100%)",
      header:
        "linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)",
      background: "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)",
      backgroundSubtle:
        "linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%)",
    },
    alpha: {
      card: "rgba(139, 92, 246, 0.05)",
      cardBorder: "rgba(139, 92, 246, 0.2)",
      hover: "rgba(139, 92, 246, 0.1)",
      divider: "rgba(139, 92, 246, 0.2)",
    },
  },
  green: {
    primary: {
      main: "#10b981", // Emerald
      light: "#34d399",
      dark: "#059669",
    },
    secondary: {
      main: "#14b8a6", // Teal
      light: "#5eead4",
      dark: "#0d9488",
    },
    gradients: {
      primary: "linear-gradient(135deg, #14b8a6 0%, #10b981 100%)",
      primaryLight: "linear-gradient(135deg, #5eead4 0%, #34d399 100%)",
      header:
        "linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)",
      background: "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)",
      backgroundSubtle:
        "linear-gradient(135deg, rgba(20, 184, 166, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%)",
    },
    alpha: {
      card: "rgba(16, 185, 129, 0.05)",
      cardBorder: "rgba(16, 185, 129, 0.2)",
      hover: "rgba(16, 185, 129, 0.1)",
      divider: "rgba(16, 185, 129, 0.2)",
    },
  },
  blue: {
    primary: {
      main: "#3b82f6", // Blue
      light: "#60a5fa",
      dark: "#2563eb",
    },
    secondary: {
      main: "#06b6d4", // Cyan
      light: "#22d3ee",
      dark: "#0891b2",
    },
    gradients: {
      primary: "linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)",
      primaryLight: "linear-gradient(135deg, #22d3ee 0%, #60a5fa 100%)",
      header:
        "linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)",
      background: "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)",
      backgroundSubtle:
        "linear-gradient(135deg, rgba(6, 182, 212, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%)",
    },
    alpha: {
      card: "rgba(59, 130, 246, 0.05)",
      cardBorder: "rgba(59, 130, 246, 0.2)",
      hover: "rgba(59, 130, 246, 0.1)",
      divider: "rgba(59, 130, 246, 0.2)",
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
export function getThemeColors(themeName = "purple") {
  return THEME_COLORS[themeName] || THEME_COLORS.purple;
}

/**
 * Create MUI theme configuration for a specific color theme
 * @param {string} themeName - Name of the theme (purple, green, blue)
 * @param {boolean} isDark - Whether dark mode is enabled
 * @returns {object} MUI theme palette configuration
 */
export function createThemePalette(themeName = "purple", isDark = true) {
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
