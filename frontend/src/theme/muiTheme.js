/**
 * Material-UI theme configuration
 *
 * Centralized theme creation with component overrides, palette, and typography.
 * Extracted from main.jsx for better maintainability and reusability.
 */

import { createTheme } from "@mui/material";
import { createThemePalette } from "./themes";
import { COMMON_COLORS } from "./colors";
import { TRANSITIONS } from "./styles";

/**
 * Create component style overrides
 * @param {boolean} prefersDarkMode - System dark mode preference
 * @param {object} themeColors - Current theme color palette
 * @returns {object} MUI component overrides
 */
function createComponentOverrides(prefersDarkMode, themeColors) {
  return {
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          transition: TRANSITIONS.cubic,
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.primary.main,
            borderWidth: 2,
            transition: TRANSITIONS.cubic,
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.main,
            boxShadow: `
              0 0 8px ${themeColors.alpha.hover},
              0 0 16px ${themeColors.primary.main}40,
              0 0 24px ${themeColors.secondary.main}20
            `,
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.light,
            borderWidth: 2,
            boxShadow: `
              0 0 10px ${themeColors.alpha.hover},
              0 0 20px ${themeColors.primary.main}60,
              0 0 30px ${themeColors.secondary.main}40,
              inset 0 0 15px ${themeColors.alpha.card}
            `,
          },
        },
      },
    },

    MuiSelect: {
      styleOverrides: {
        root: {
          transition: TRANSITIONS.cubic,
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.primary.main,
            borderWidth: 2,
            transition: TRANSITIONS.cubic,
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.main,
            boxShadow: `
              0 0 8px ${themeColors.alpha.hover},
              0 0 16px ${themeColors.primary.main}40,
              0 0 24px ${themeColors.secondary.main}20
            `,
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.light,
            borderWidth: 2,
            boxShadow: `
              0 0 10px ${themeColors.alpha.hover},
              0 0 20px ${themeColors.primary.main}60,
              0 0 30px ${themeColors.secondary.main}40,
              inset 0 0 15px ${themeColors.alpha.card}
            `,
          },
        },
      },
    },

    MuiInputLabel: {
      styleOverrides: {
        root: {
          color: COMMON_COLORS.text.muted,
          transition: TRANSITIONS.cubic,
          "&.Mui-focused": {
            color: themeColors.secondary.light,
          },
        },
      },
    },

    MuiInputBase: {
      styleOverrides: {
        root: {
          color: COMMON_COLORS.text.secondary,
          transition: TRANSITIONS.cubic,
        },
      },
    },

    MuiSvgIcon: {
      styleOverrides: {
        root: {
          transition: TRANSITIONS.cubic,
        },
      },
    },

    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: prefersDarkMode
            ? themeColors.gradients.background
            : "#ffffff",
          borderRadius: "0 16px 16px 0",
          border: "none",
          borderRight: `1px solid ${prefersDarkMode ? "#334155" : "#e2e8f0"}`,
          boxShadow: "4px 0 24px rgba(0, 0, 0, 0.15)",
          transition: TRANSITIONS.cubic,
        },
      },
    },

    MuiAppBar: {
      styleOverrides: {
        root: {
          background: prefersDarkMode
            ? "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)"
            : themeColors.gradients.primary,
          backdropFilter: "blur(10px)",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.2)",
          borderBottom: `1px solid ${
            prefersDarkMode ? "#334155" : "rgba(255,255,255,0.1)"
          }`,
          transition: TRANSITIONS.cubic,
        },
      },
    },

    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: "8px",
          textTransform: "none",
          fontWeight: 600,
          transition: TRANSITIONS.cubic,
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: `0 6px 20px ${themeColors.alpha.hover}`,
          },
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          transition: TRANSITIONS.cubic,
        },
      },
    },

    MuiListItem: {
      styleOverrides: {
        root: {
          transition: TRANSITIONS.cubic,
          borderRadius: "8px",
          margin: "4px 8px",
        },
      },
    },
  };
}

/**
 * Create typography configuration
 * @returns {object} Typography settings
 */
function createTypography() {
  return {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h5: {
      fontWeight: 700,
      letterSpacing: "-0.02em",
    },
    h6: {
      fontWeight: 600,
      letterSpacing: "-0.01em",
    },
  };
}

/**
 * Create complete MUI theme
 * @param {string} themeName - Theme name (purple, green, blue)
 * @param {boolean} prefersDarkMode - System dark mode preference
 * @param {object} themeColors - Current theme color palette
 * @returns {object} Complete MUI theme
 */
export function createMuiTheme(themeName, prefersDarkMode, themeColors) {
  return createTheme({
    palette: createThemePalette(themeName, prefersDarkMode),
    components: createComponentOverrides(prefersDarkMode, themeColors),
    typography: createTypography(),
  });
}
