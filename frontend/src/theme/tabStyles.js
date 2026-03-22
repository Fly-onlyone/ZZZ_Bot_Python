// Shared Aurora tab styles — used across Shopping, Settings, Account, Tools pages

/**
 * Get Aurora-styled Tabs sx prop with luminous glow underline
 */
export function getAuroraTabsStyles(themeColors) {
  return {
    mb: 3,
    minHeight: 48,
    "& .MuiTabs-indicator": { display: "none" },
    "& .MuiTab-root": {
      minHeight: 48,
      minWidth: "auto",
      px: 2.5,
      color: "text.secondary",
      fontWeight: 600,
      textTransform: "none",
      position: "relative",
      "&::after": {
        content: '""',
        position: "absolute",
        left: 12,
        right: 12,
        bottom: 0,
        height: 3,
        borderRadius: "999px",
        backgroundColor: "transparent",
        boxShadow: "none",
        transition: "all 0.3s ease",
      },
      "&.Mui-selected": {
        color: themeColors.primary.light,
      },
      "&.Mui-selected::after": {
        backgroundColor: themeColors.primary.main,
        boxShadow: `0 0 12px ${themeColors.glow}50, 0 2px 8px ${themeColors.glow}30`,
      },
    },
  };
}

/**
 * Panel transition variants for tab content
 */
export const auroraPanelVariants = {
  initial: (direction) => ({
    opacity: 0,
    x: direction * 20,
    scale: 0.995,
  }),
  animate: {
    opacity: 1,
    x: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 140,
      damping: 22,
      mass: 0.9,
    },
  },
  exit: (direction) => ({
    opacity: 0,
    x: direction * -20,
    scale: 0.995,
    transition: {
      duration: 0.18,
      ease: "easeInOut",
    },
  }),
};

/**
 * Reduced motion variant — fade only
 */
export const reducedMotionPanelVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.12, ease: "easeOut" },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.08, ease: "easeInOut" },
  },
};
