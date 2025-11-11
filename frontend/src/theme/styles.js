// Common style utilities for consistent component styling
import { ALPHA, COLORS, GRADIENTS } from "./colors";

// Common transitions
export const TRANSITIONS = {
  default: "all 0.3s ease-in-out",
  fast: "all 0.2s ease-in-out",
  cubic: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
};

// Button styles
export const buttonStyles = {
  primary: {
    background: GRADIENTS.primary,
    color: "#ffffff",
    fontWeight: 600,
    borderRadius: "8px",
    transition: TRANSITIONS.default,
    "&:hover": {
      background: GRADIENTS.primaryLight,
      transform: "translateY(-2px)",
      boxShadow: "0 6px 20px rgba(139, 92, 246, 0.4)",
    },
  },
  success: {
    background: GRADIENTS.success,
    color: "#ffffff",
    fontWeight: 600,
    "&:hover": {
      background: GRADIENTS.successDark,
    },
  },
  error: {
    background: COLORS.error.main,
    color: "#ffffff",
    fontWeight: 600,
    "&:hover": {
      background: COLORS.error.dark,
    },
  },
};

// Icon button styles
export const iconButtonStyles = {
  default: {
    color: COLORS.text.muted,
    transition: TRANSITIONS.default,
    "&:hover": {
      color: COLORS.secondary.main,
      backgroundColor: ALPHA.hover,
    },
  },
};

// Card/Paper styles
export const cardStyles = {
  default: {
    borderRadius: "16px",
    background: GRADIENTS.backgroundSubtle,
    border: `1px solid ${ALPHA.cardBorder}`,
    overflow: "hidden",
    transition: TRANSITIONS.default,
    "&:hover": {
      boxShadow: "0 8px 32px rgba(139, 92, 246, 0.15)",
      transform: "translateY(-2px)",
    },
  },
  header: {
    background: GRADIENTS.header,
    borderBottom: `1px solid ${ALPHA.cardBorder}`,
    padding: "20px 24px",
    display: "flex",
    alignItems: "center",
    gap: 2,
  },
};

// Input styles
export const inputStyles = {
  default: {
    "& .MuiOutlinedInput-root": {
      borderRadius: "10px",
    },
  },
};

// Switch styles
export const switchStyles = {
  default: {
    "& .MuiSwitch-switchBase.Mui-checked": {
      color: COLORS.secondary.main,
    },
    "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
      backgroundColor: COLORS.secondary.main,
    },
  },
};
