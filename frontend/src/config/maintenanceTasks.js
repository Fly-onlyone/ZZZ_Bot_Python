/**
 * Maintenance task definitions shared by the Backup page (for rendering the
 * cards) and the app-level MutationToastWatcher (for firing toasts when a task
 * finishes while the user is on a different page).
 */

import { IconDatabase, IconDatabaseImport, IconTrash } from "@tabler/icons-react";

export function formatCleanupSummary(report) {
  const deleted =
    report && typeof report === "object" && typeof report["deleted"] === "object"
      ? report["deleted"]
      : {};
  return (
    `Cleanup completed. Deleted ` +
    `${deleted["auth_storage_file"] || 0} auth file(s), ` +
    `${deleted["log_files"] || 0} log file(s), ` +
    `${deleted["screenshot_files"] || 0} screenshot file(s), ` +
    `${deleted["json_files"] || 0} JSON file(s).`
  );
}

export function formatMongoMigrationSummary(report) {
  if (!report || typeof report !== "object") {
    return "MongoDB migration finished.";
  }

  if (report.status === "no_source") {
    return report.message || "MongoDB not reachable — nothing to migrate.";
  }

  const summary = report.summary && typeof report.summary === "object" ? report.summary : {};
  const parts = Object.entries(summary)
    .filter(([, count]) => Number(count) > 0)
    .map(([name, count]) => `${name} (${count})`);
  const head = parts.length
    ? `Imported from MongoDB: ${parts.join(", ")}.`
    : "MongoDB connected but no rows were imported.";

  const archives = report.archives && typeof report.archives === "object" ? report.archives : null;
  const archiveKeys = archives ? Object.keys(archives) : [];
  const archiveSuffix = archiveKeys.length ? ` Archived: ${archiveKeys.join(", ")}.` : "";

  const errors = report.errors && typeof report.errors === "object" ? report.errors : null;
  const errorKeys = errors ? Object.keys(errors) : [];
  if (errorKeys.length) {
    return `${head}${archiveSuffix} Runtime refresh warnings: ${errorKeys.join(", ")}.`;
  }
  return `${head}${archiveSuffix}`;
}

export function formatCompactDbSummary(report) {
  if (!report || typeof report !== "object") {
    return "Database compacted.";
  }
  const mb = (value) => (Number(value || 0) / (1024 * 1024)).toFixed(1);
  return (
    `Database compacted. Reclaimed ${mb(report.reclaimed_bytes)} MB ` +
    `(${mb(report.size_before)} MB → ${mb(report.size_after)} MB).`
  );
}

export const MAINTENANCE_TASKS = [
  {
    key: "mongo-migration",
    icon: IconDatabaseImport,
    title: "Migrate from MongoDB",
    description: "Import existing local MongoDB data into the SQLite database",
    route: "maintenance/mongo-migration",
    formatSuccess: formatMongoMigrationSummary,
    errorMessage: "Failed to run MongoDB migration.",
  },
  {
    key: "local-cleanup",
    icon: IconTrash,
    title: "Local Cleanup",
    description: "Remove local artifacts and screenshots",
    route: "maintenance/local-cleanup",
    formatSuccess: formatCleanupSummary,
    errorMessage: "Failed to run local cleanup.",
  },
  {
    key: "compact-db",
    icon: IconDatabase,
    title: "Compact Database",
    description: "Purge expired rows and VACUUM to reclaim disk space",
    route: "maintenance/compact-db",
    formatSuccess: formatCompactDbSummary,
    errorMessage: "Failed to compact the database.",
  },
];
