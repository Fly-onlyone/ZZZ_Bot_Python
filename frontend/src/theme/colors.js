// Theme color constants for consistent styling across the application

export const COLORS = {
  // Primary - Indigo/Purple
  primary: {
    main: "#6366f1",
    light: "#818cf8",
    dark: "#4f46e5",
  },
  secondary: {
    main: "#8b5cf6",
    light: "#a78bfa",
    dark: "#7c3aed",
  },

  // Semantic colors
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

  // Text colors
  text: {
    primary: "#f1f5f9",
    secondary: "#e2e8f0",
    tertiary: "#cbd5e1",
    muted: "#94a3b8",
  },

  // Background colors
  background: {
    dark: "#0f172a",
    paper: "#1e293b",
    slate: "#334155",
  },
};

// Gradient definitions
export const GRADIENTS = {
  primary: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
  primaryLight: "linear-gradient(135deg, #a78bfa 0%, #818cf8 100%)",
  success: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
  successDark: "linear-gradient(135deg, #059669 0%, #047857 100%)",
  background: "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)",
  backgroundSubtle:
    "linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(99, 102, 241, 0.05) 100%)",
  header:
    "linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)",
};

// Common alpha values for transparency
export const ALPHA = {
  card: "rgba(139, 92, 246, 0.05)",
  cardBorder: "rgba(139, 92, 246, 0.2)",
  hover: "rgba(139, 92, 246, 0.1)",
  divider: "rgba(139, 92, 246, 0.2)",
};
