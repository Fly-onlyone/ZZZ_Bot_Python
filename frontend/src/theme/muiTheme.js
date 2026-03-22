/**
 * Material-UI theme configuration
 *
 * Centralized theme creation with component overrides, palette, and typography.
 * Extracted from main.jsx for better maintainability and reusability.
 */

import { createTheme } from "@mui/material";
import { createThemePalette } from "./themes";
import { COMMON_COLORS } from "./colors";
import { GLOW, TRANSITIONS } from "./styles";

/**
 * Create component style overrides
 * @param {boolean} prefersDarkMode - System dark mode preference
 * @param {object} themeColors - Current theme color palette
 * @returns {object} MUI component overrides
 */
function createComponentOverrides(prefersDarkMode, themeColors) {
  const outlinedInputStyles = {
    transition: TRANSITIONS.cubic,
    "& .MuiOutlinedInput-notchedOutline": {
      borderColor: themeColors.alpha.cardBorder,
      borderWidth: 1,
      transition: TRANSITIONS.cubic,
    },
    "&:hover .MuiOutlinedInput-notchedOutline": {
      borderColor: themeColors.primary.main,
      boxShadow: `0 0 18px ${themeColors.glow}35`,
    },
    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
      borderColor: themeColors.primary.main,
      borderWidth: 2,
      boxShadow: `0 0 25px ${themeColors.glow}45, 0 0 8px ${themeColors.glow}25`,
    },
  };

  return {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          overflowX: "hidden",
          scrollbarColor: prefersDarkMode
            ? "#334155 #0f172a"
            : "#cbd5e1 #f1f5f9",
          "&::-webkit-scrollbar, & *::-webkit-scrollbar": {
            width: "8px",
            height: "0px",
          },
          "&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb": {
            borderRadius: 8,
            minHeight: 24,
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: outlinedInputStyles,
      },
    },

    MuiSelect: {
      styleOverrides: {
        root: outlinedInputStyles,
      },
    },

    MuiInputLabel: {
      styleOverrides: {
        root: {
          color: COMMON_COLORS.text.muted,
          fontFamily: '"Outfit", sans-serif',
          transition: TRANSITIONS.cubic,
          "&.Mui-focused": {
            color: themeColors.primary.main,
          },
        },
      },
    },

    MuiInputBase: {
      styleOverrides: {
        root: {
          color: COMMON_COLORS.text.primary,
          fontFamily: '"Inter", sans-serif',
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
            ? `linear-gradient(180deg, ${themeColors.glow}30 0%, rgba(15, 23, 42, 0.15) 40%, ${themeColors.glow}20 100%)`
            : "#ffffff",
          backdropFilter: "blur(24px)",
          overflowX: "hidden",
          borderRadius: "0 24px 24px 0",
          border: "none",
          borderRight: `1px solid ${themeColors.glow}30`,
          boxShadow: `8px 0 50px ${themeColors.glow}25, 3px 0 20px ${themeColors.glow}18`,
          transition: TRANSITIONS.cubic,
          "&::after": {
            content: '""',
            position: "absolute",
            top: "5%",
            right: -1,
            bottom: "5%",
            width: "2px",
            background: `linear-gradient(180deg, transparent, ${themeColors.glow}70, ${themeColors.primary.light}50, ${themeColors.glow}70, transparent)`,
            borderRadius: "2px",
            filter: "blur(1px)",
            pointerEvents: "none",
          },
        },
      },
    },

    MuiAppBar: {
      styleOverrides: {
        root: {
          background: "rgba(15, 23, 42, 0.2)",
          backdropFilter: "blur(20px)",
          boxShadow: `0 4px 40px ${themeColors.glow}18, 0 1px 3px rgba(0,0,0,0.3)`,
          borderBottom: `1px solid ${themeColors.glow}30`,
          transition: TRANSITIONS.cubic,
          "&::after": {
            content: '""',
            position: "absolute",
            bottom: -1,
            left: "5%",
            right: "5%",
            height: "2px",
            background: `linear-gradient(90deg, transparent, ${themeColors.glow}70, ${themeColors.primary.light}50, ${themeColors.glow}70, transparent)`,
            borderRadius: "2px",
            filter: `blur(1px)`,
            pointerEvents: "none",
          },
        },
      },
    },

    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: "12px",
          textTransform: "none",
          fontFamily: '"Outfit", sans-serif',
          fontWeight: 600,
          transition: TRANSITIONS.cubic,
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: `0 4px 12px ${themeColors.alpha.hover}`,
          },
        },
        contained: {
          background: themeColors.gradients.primary,
          boxShadow: GLOW.subtle(themeColors.glow),
          "&:hover": {
            background: themeColors.gradients.primaryLight,
            boxShadow: GLOW.medium(themeColors.glow),
          },
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          transition: TRANSITIONS.cubic,
          "&.MuiMenu-paper": {
            background: prefersDarkMode
              ? "rgba(30, 41, 59, 0.8)"
              : "rgba(255, 255, 255, 0.9)",
            backdropFilter: "blur(16px)",
            border: `1px solid ${themeColors.alpha.divider}`,
            borderRadius: "16px",
            boxShadow: `0 8px 32px ${themeColors.alpha.cardBorder}`,
          },
        },
      },
    },

    MuiDataGrid: {
      styleOverrides: {
        root: {
          border: `1px solid ${themeColors.alpha.cardBorder}`,
          borderRadius: "16px",
          background: themeColors.alpha.card,
          backdropFilter: "blur(8px)",
          color: COMMON_COLORS.text.primary,
          "& .MuiDataGrid-cell": {
            borderBottom: `1px solid ${themeColors.alpha.divider}`,
          },
          "& .MuiDataGrid-columnHeaders": {
            backgroundColor: `${themeColors.alpha.card} !important`,
            borderBottom: `1px solid ${themeColors.alpha.divider}`,
            color: themeColors.primary.light,
            fontSize: "0.95rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            "& > div": {
              backgroundColor: `${themeColors.alpha.card} !important`,
            },
          },
          "& .MuiDataGrid-footerContainer": {
            borderTop: `1px solid ${themeColors.alpha.divider}`,
            backgroundColor: `${themeColors.alpha.card} !important`,
            color: COMMON_COLORS.text.secondary,
          },
          "& .MuiDataGrid-row:hover": {
            background: themeColors.alpha.hover,
          },
          "& .MuiDataGrid-row.Mui-selected": {
            background: `${themeColors.primary.main}1A`, // 10% opacity
            "&:hover": {
              background: `${themeColors.primary.main}26`, // 15% opacity
            },
          },
          "& .MuiCheckbox-root": {
            color: themeColors.alpha.divider,
            "&.Mui-checked": {
              color: themeColors.primary.main,
            },
          },
        },
      },
    },

    MuiListItem: {
      styleOverrides: {
        root: {
          transition: TRANSITIONS.cubic,
          borderRadius: "12px",
          margin: "4px 8px",
          "&:hover": {
            background: themeColors.alpha.hover,
          },
        },
      },
    },

    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: "12px",
          transition: TRANSITIONS.cubic,
          "&.Mui-selected": {
            background: themeColors.alpha.hover,
            border: `1px solid ${themeColors.alpha.divider}`,
            "&:hover": {
              background: themeColors.alpha.hover,
            },
          },
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
    h1: { fontFamily: '"Outfit", sans-serif', fontWeight: 700 },
    h2: { fontFamily: '"Outfit", sans-serif', fontWeight: 700 },
    h3: { fontFamily: '"Outfit", sans-serif', fontWeight: 600 },
    h4: { fontFamily: '"Outfit", sans-serif', fontWeight: 600 },
    h5: {
      fontFamily: '"Outfit", sans-serif',
      fontWeight: 600,
      letterSpacing: "-0.01em",
    },
    h6: {
      fontFamily: '"Outfit", sans-serif',
      fontWeight: 600,
      letterSpacing: "0.01em",
    },
    button: {
      fontFamily: '"Outfit", sans-serif',
      fontWeight: 600,
    },
  };
}

/**
 * Create complete MUI theme
 * @param {string} themeName - Theme name (purple, green, blue, cyber)
 * @param {boolean} prefersDarkMode - System dark mode preference
 * @param {object} themeColors - Current theme color palette
 * @returns {object} Complete MUI theme
 */
export function createMuiTheme(themeName, prefersDarkMode, themeColors) {
  return createTheme({
    palette: createThemePalette(themeName, prefersDarkMode),
    components: createComponentOverrides(prefersDarkMode, themeColors),
    typography: createTypography(),
    shape: {
      borderRadius: 12,
    },
  });
}
