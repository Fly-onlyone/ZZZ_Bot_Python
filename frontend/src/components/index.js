/**
 * Components Index
 *
 * Central export point for all reusable components.
 * Enables clean imports: import { SaveStatus, ArrayField } from '@/components';
 */

// Common Components
export { default as EmptyState } from "./common/EmptyState.jsx";
export { default as SaveStatus } from "./common/SaveStatus.jsx";
export { default as SectionCard } from "./common/SectionCard.jsx";
export { default as ShoppingItemsTable } from "./common/ShoppingItemsTable.jsx";
export { default as DataTable } from "./common/DataTable.jsx";
export { default as NotificationProvider } from "./common/NotificationProvider.jsx";
export { default as MutationToastWatcher } from "./common/MutationToastWatcher.jsx";
export { useNotification } from "./common/NotificationContext.js";

// Skeleton Components
export {
  BackupSkeleton,
  HuntSkeleton,
  LogsSkeleton,
  MissionSkeleton,
  RedeemSkeleton,
  RunningStatusSkeleton,
  SettingsSkeleton,
  ShoppingSkeleton,
} from "./common/Skeleton";

// Field Components
export { default as ArrayField } from "./fields/ArrayField.jsx";
export { default as BooleanField } from "./fields/BooleanField.jsx";
export { default as SelectField } from "./fields/SelectField.jsx";
export { default as TextField } from "./fields/TextField.jsx";

// Layout Components
export { default as AppHeader } from "./layout/AppHeader.jsx";
export { default as NavigationDrawer } from "./layout/NavigationDrawer.jsx";
export { default as ThemePicker } from "./layout/ThemePicker.jsx";

// Form Components
export { default as ValueAdapter } from "./forms/ValueAdapter.jsx";
