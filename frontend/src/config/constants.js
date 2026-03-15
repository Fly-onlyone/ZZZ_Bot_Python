/**
 * Frontend Application Constants
 *
 * Centralized configuration values for the ZZZ Bot frontend.
 * Eliminates magic numbers and provides a single source of truth.
 */

// ============================================================================
// API CONFIGURATION
// ============================================================================

/**
 * Backend API base URL
 * Uses environment variable if available, falls back to localhost
 */
export const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000";

// ============================================================================
// CACHE/STALE TIME CONFIGURATION (milliseconds)
// ============================================================================

/**
 * Data staleness times for React Query caching
 * Longer times = less frequent refetching = better performance
 */
export const STALE_TIMES = {
  shopping: 1000 * 60 * 15, // 15 minutes (shopping data changes hourly)
  redeem: 1000 * 60 * 10, // 10 minutes (redemption codes)
  settings: 1000 * 60 * 60, // 1 hour (rarely changes)
  account: 1000 * 60 * 30, // 30 minutes (account credentials)
  "overview/mission": 1000 * 60 * 5, // 5 minutes (mission reports)
  "overview/hunt": 1000 * 60 * 5, // 5 minutes (hunt mode status)
  "backup/summary": 1000 * 60 * 2, // 2 minutes (backup page metadata)
  "backup/config": 1000 * 60 * 60, // 1 hour (backup export path, rarely changes)
  "locator-tracker": 1000 * 60 * 2, // 2 minutes (locator tracker data)
  "locator-tracker/failures": 1000 * 60 * 2, // 2 minutes (locator tracker failures)
};

/**
 * Default stale time for routes not specified above
 */
export const DEFAULT_STALE_TIME = 1000 * 60; // 1 minute

// ============================================================================
// LAYOUT CONSTANTS
// ============================================================================

/**
 * Navigation drawer width in pixels
 */
export const DRAWER_WIDTH = 240;

/**
 * App bar (header) height in pixels
 */
export const HEADER_HEIGHT = 64;

// ============================================================================
// PRIORITY MANAGEMENT
// ============================================================================

/**
 * Default offset when assigning priorities to items
 * Priority starts at 1 (index + DEFAULT_PRIORITY_OFFSET)
 */
export const DEFAULT_PRIORITY_OFFSET = 1;

// ============================================================================
// RETRY CONFIGURATION
// ============================================================================

/**
 * Number of times to retry failed API requests
 */
export const API_RETRY_COUNT = 2;

// ============================================================================
// FORM FIELD DETECTION
// ============================================================================

/**
 * Keywords to detect password fields for special rendering
 */
export const PASSWORD_FIELD_KEYWORDS = ["password"];

// ============================================================================
// UI CONSTANTS
// ============================================================================

/**
 * Border radius for cards and panels
 */
export const CARD_BORDER_RADIUS = "16px";

/**
 * Icon badge size
 */
export const ICON_BADGE_SIZE = 40;

/**
 * Default padding for main content
 */
export const MAIN_CONTENT_PADDING = 6; // MUI spacing units (6 * 8px = 48px)

// ============================================================================
// TABLE/GRID CONFIGURATION
// ============================================================================

/**
 * Default page size for data grids
 */
export const DEFAULT_PAGE_SIZE = 10;

/**
 * Available page size options for data grids
 */
export const PAGE_SIZE_OPTIONS = [5, 10, 20, 50];

// ============================================================================
// NOTIFICATION/ALERT DURATIONS (milliseconds)
// ============================================================================

/**
 * How long to show success/error alerts
 */
export const ALERT_DURATION = 3000; // 3 seconds

// ============================================================================
// THEME CONSTANTS
// ============================================================================

/**
 * Available theme options
 */
export const THEME_OPTIONS = [
  { value: "purple", label: "Purple" },
  { value: "green", label: "Green" },
  { value: "blue", label: "Blue" },
];

/**
 * Default theme
 */
export const DEFAULT_THEME = "purple";
