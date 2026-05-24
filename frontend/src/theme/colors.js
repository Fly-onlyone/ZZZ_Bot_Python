// Theme color constants for consistent styling across the application
// NOTE: This file now re-exports from themes.js for backward compatibility
// For new code, import directly from './themes'

import { COMMON_COLORS, THEME_COLORS } from "./themes";

// Export default nebula theme colors for backward compatibility
const defaultTheme = THEME_COLORS.nebula;

export const COLORS = {
  // Primary - from selected theme (defaults to nebula)
  primary: defaultTheme.primary,
  secondary: defaultTheme.secondary,

  // Semantic colors (common across all themes)
  success: COMMON_COLORS.success,
  error: COMMON_COLORS.error,
  warning: COMMON_COLORS.warning,
  info: COMMON_COLORS.info,

  // Text colors
  text: COMMON_COLORS.text,

  // Background colors
  background: COMMON_COLORS.background,
};

// Gradient definitions (defaults to nebula theme)
export const GRADIENTS = defaultTheme.gradients;

// Common alpha values for transparency
export const ALPHA = defaultTheme.alpha;

// Re-export theme utilities
export { THEME_COLORS, COMMON_COLORS, getThemeColors } from "./themes";
