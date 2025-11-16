// Theme color constants for consistent styling across the application
// NOTE: This file now re-exports from themes.js for backward compatibility
// For new code, import directly from './themes'

import { THEME_COLORS, COMMON_COLORS, getThemeColors } from "./themes";

// Export default purple theme colors for backward compatibility
const purpleTheme = THEME_COLORS.purple;

export const COLORS = {
  // Primary - from selected theme (defaults to purple)
  primary: purpleTheme.primary,
  secondary: purpleTheme.secondary,

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

// Gradient definitions (defaults to purple theme)
export const GRADIENTS = purpleTheme.gradients;

// Common alpha values for transparency
export const ALPHA = purpleTheme.alpha;

// Re-export theme utilities
export { THEME_COLORS, COMMON_COLORS, getThemeColors } from "./themes";
