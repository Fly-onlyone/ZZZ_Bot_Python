/**
 * Shared animation variants for consistent animations across components
 * Define variants here to avoid duplication and ensure they're only created once
 */

// ============================================================
// Container Variants (for staggered children)
// ============================================================

export const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      when: "beforeChildren",
    },
  },
};

// ============================================================
// Card Variants
// ============================================================

export const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
};

/**
 * Card variants with custom delay based on index
 */
export const indexedCardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.1,
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1],
    },
  }),
};

// ============================================================
// Table Row Variants
// ============================================================

export const tableRowVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (index) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: index * 0.05,
      type: "spring",
      stiffness: 100,
      damping: 15,
    },
  }),
};

// ============================================================
// Item Variants (for list items)
// ============================================================

export const itemVariants = {
  hidden: { opacity: 0, y: 15 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
};

// ============================================================
// Icon Variants
// ============================================================

export const iconVariants = {
  hidden: { opacity: 0, scale: 0.8, rotate: -10 },
  visible: {
    opacity: 1,
    scale: 1,
    rotate: 0,
    transition: { type: "spring", stiffness: 200, damping: 15 },
  },
  hover: {
    scale: 1.1,
    rotate: 5,
    transition: { duration: 0.3, ease: "easeOut" },
  },
};

// ============================================================
// Image/Media Variants
// ============================================================

export const imageVariants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: { duration: 0.2 },
  },
};

// ============================================================
// Schedule/Info Box Variants
// ============================================================

export const scheduleBoxVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: { duration: 0.2 },
  },
};

// ============================================================
// List Item Variants (for navigation)
// ============================================================

export const listItemVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: i * 0.1,
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1],
    },
  }),
  hover: {
    scale: 1.02,
    transition: { duration: 0.2, ease: "easeOut" },
  },
  tap: {
    scale: 0.98,
  },
};

// ============================================================
// Button Variants
// ============================================================

export const buttonVariants = {
  initial: { scale: 1 },
  hover: { scale: 1.05 },
  tap: { scale: 0.95 },
};

export const buttonIconVariants = {
  hover: {
    rotate: [0, -10, 10, -10, 0],
    transition: { duration: 0.5 },
  },
};
