// Common style utilities for consistent component styling

// Common transitions
export const TRANSITIONS = {
  default: "all 0.3s ease-in-out",
  fast: "all 0.2s ease-in-out",
  cubic: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
};

// Luminous glow effects — pass theme glow color
export const GLOW = {
  subtle: (color) => `0 0 25px ${color}30, 0 4px 35px ${color}20`,
  medium: (color) => `0 0 35px ${color}45, 0 4px 45px ${color}30`,
  strong: (color) => `0 0 50px ${color}55, 0 8px 60px ${color}35`,
  border: (color) => `0 0 18px ${color}50`,
  text: (color) => `0 0 20px ${color}50`,
};
