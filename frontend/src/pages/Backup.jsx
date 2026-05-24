import React, { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  FormControlLabel,
  InputBase,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { motion } from "framer-motion";
import {
  IconClock,
  IconDatabaseExport,
  IconDatabaseImport,
  IconFile,
  IconFolder,
  IconFolderOpen,
  IconInfoCircle,
  IconTool,
} from "@tabler/icons-react";

import { BackupSkeleton, SectionCard, useNotification } from "../components";
import { MAINTENANCE_TASKS } from "../config/maintenanceTasks";
import { BACKEND_URL } from "../config";
import { DataLoader } from "../services";
import { logError, logInfo } from "../services/sentryLogger.js";
import { GLOW, TRANSITIONS } from "../theme/styles";
import { COMMON_COLORS } from "../theme/colors";
import { useThemeContext } from "../theme/ThemeContext";

/**
 * @typedef {{
 *   exists?: boolean,
 *   count?: number,
 *   field_count?: number,
 * }} SummaryInfo
 */

/**
 * @typedef {Record<string, SummaryInfo>} BackupSummary
 */

/**
 * @typedef {{
 *   version: number,
 *   exported_at: string,
 *   collections: Record<string, unknown>,
 * }} BackupPayload
 */

const ALL_COLLECTIONS = ["settings", "account", "shopping", "redemptions", "missions", "last_run"];

const cardVariants = {
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

function DataSummary({ summary }) {
  /** @type {BackupSummary} */
  const resolvedSummary = summary || {};

  /** @type {React.ReactNode[]} */
  const summaryRows = ALL_COLLECTIONS.map((name) => {
    const info = resolvedSummary[name] || {};
    return (
      <TableRow key={name}>
        <TableCell sx={{ textTransform: "capitalize" }}>{name.replace("_", " ")}</TableCell>
        <TableCell>
          <Chip
            label={info.exists ? "Has data" : "Empty"}
            color={info.exists ? "success" : "default"}
            size="small"
            variant="outlined"
          />
        </TableCell>
        <TableCell align="right">
          {info.count !== undefined
            ? `${info.count} record(s)`
            : info["field_count"] !== undefined
              ? `${info["field_count"]} field(s)`
              : "-"}
        </TableCell>
      </TableRow>
    );
  });

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Collection</TableCell>
            <TableCell>Status</TableCell>
            <TableCell align="right">Details</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>{summaryRows}</TableBody>
      </Table>
    </TableContainer>
  );
}

function ExportSection({ showAlert }) {
  const { themeColors } = useThemeContext();
  const { useRouteData, useActionData } = DataLoader();
  const { data: config } = useRouteData("backup/config");
  const saveConfigMutation = useActionData("backup/config");
  const exportMutation = useActionData("backup/export");

  const [exportPath, setExportPath] = useState("");

  // Sync from server config on load
  useEffect(() => {
    if (config?.export_path != null) {
      setExportPath(config.export_path);
    }
  }, [config?.export_path]);

  const handleBrowse = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/backup/browse`, {
        method: "POST",
      });
      const result = await response.json();
      if (result.cancelled || !result.path) {
        return;
      }
      setExportPath(result.path);
      await savePath(result.path);
      logInfo("Backup export path selected", { path: result.path });
    } catch (error) {
      showAlert("error", error instanceof Error ? error.message : "Failed to open folder picker.");
    }
  };

  const handleExport = async () => {
    try {
      // Ensure typed path is saved before exporting
      await savePath(undefined, { silent: true });
      const result = await exportMutation.mutateAsync({});
      logInfo("Backup exported successfully", { file: result?.file });
      showAlert("success", `Backup saved to ${result?.file}`);
    } catch (error) {
      logError("Backup export failed", error);
      showAlert("error", error instanceof Error ? error.message : "Export failed.");
    }
  };

  const savePath = async (path, { silent = false } = {}) => {
    const trimmed = (path ?? exportPath).trim();
    if (!trimmed || trimmed === (config?.export_path ?? "")) {
      return;
    }
    try {
      await saveConfigMutation.mutateAsync({ export_path: trimmed });
      if (!silent) {
        showAlert("success", "Export folder set.");
      }
      logInfo("Backup export path saved", { path: trimmed });
    } catch (error) {
      showAlert("error", error instanceof Error ? error.message : "Failed to save export path.");
    }
  };

  const handlePathKeyDown = (e) => {
    if (e.key === "Enter") {
      e.target.blur();
    }
  };

  const pathEmpty = !exportPath.trim();

  const outlinedButtonSx = {
    whiteSpace: "nowrap",
    borderColor: `${themeColors.primary.main}80`,
    color: themeColors.primary.light,
    backdropFilter: "blur(8px)",
    transition: TRANSITIONS.cubic,
    "&:hover": {
      borderColor: themeColors.primary.main,
      background: `${themeColors.primary.main}15`,
      boxShadow: `0 0 25px ${themeColors.primary.main}30`,
    },
  };

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Set the folder where backups will be saved, then export.
      </Typography>

      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2.5 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={handleBrowse}
          startIcon={<IconFolderOpen size={16} />}
          sx={outlinedButtonSx}
        >
          Choose Folder
        </Button>
        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            px: 2,
            py: 0.5,
            borderRadius: "10px",
            background: themeColors.alpha.card,
            border: `1px solid ${themeColors.alpha.cardBorder}`,
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            gap: 1,
            transition: TRANSITIONS.cubic,
            "&:focus-within": {
              borderColor: themeColors.primary.main,
              boxShadow: `0 0 15px ${themeColors.primary.main}20`,
            },
          }}
        >
          <IconFolder
            size={16}
            color={exportPath ? themeColors.primary.light : COMMON_COLORS.text.muted}
            style={{ flexShrink: 0 }}
          />
          <InputBase
            value={exportPath}
            onChange={(e) => setExportPath(e.target.value)}
            onBlur={() => savePath()}
            onKeyDown={handlePathKeyDown}
            placeholder="No folder selected"
            fullWidth
            sx={{
              fontSize: "0.875rem",
              color: "text.primary",
              "& input::placeholder": {
                color: COMMON_COLORS.text.muted,
                opacity: 1,
              },
            }}
          />
        </Box>
      </Box>

      <Button
        variant="contained"
        disabled={pathEmpty || exportMutation.isPending || saveConfigMutation.isPending}
        onClick={handleExport}
        startIcon={
          exportMutation.isPending ? (
            <CircularProgress size={18} color="inherit" />
          ) : (
            <IconDatabaseExport size={18} />
          )
        }
        sx={{
          background: themeColors.gradients.primary,
          color: "#0f172a",
          fontWeight: 600,
          boxShadow: GLOW.subtle(themeColors.glow),
          transition: TRANSITIONS.cubic,
          "&:hover": {
            background: themeColors.gradients.primaryLight,
            boxShadow: GLOW.medium(themeColors.glow),
            transform: "translateY(-2px)",
          },
        }}
      >
        {exportMutation.isPending ? "Exporting..." : "Export Backup"}
      </Button>
    </Box>
  );
}

function RestoreSection({ showAlert }) {
  const { themeColors } = useThemeContext();
  const fileInputRef = useRef(null);
  /** @type {[BackupPayload | null, React.Dispatch<React.SetStateAction<BackupPayload | null>>]} */
  const [backupData, setBackupData] = useState(null);
  const [fileName, setFileName] = useState("");
  const [selected, setSelected] = useState([]);
  const [importing, setImporting] = useState(false);

  const { useActionData } = DataLoader();
  const importMutation = useActionData("backup/import");

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const rawResult = e.target?.result;
        if (typeof rawResult !== "string") {
          showAlert("error", "Could not read backup file.");
          setBackupData(null);
          return;
        }

        /** @type {BackupPayload} */
        const parsed = JSON.parse(rawResult);
        if (parsed.version !== 1 || !parsed.collections) {
          showAlert("error", "Invalid backup file format.");
          setBackupData(null);
          return;
        }
        setBackupData(parsed);
        setSelected(ALL_COLLECTIONS.filter((c) => parsed.collections[c] != null));
      } catch {
        showAlert("error", "Could not parse JSON file.");
        setBackupData(null);
      }
    };
    reader.readAsText(file);
    event.target.value = "";
  };

  const toggleCollection = (name) => {
    setSelected((prev) => (prev.includes(name) ? prev.filter((c) => c !== name) : [...prev, name]));
  };

  const handleRestore = async () => {
    if (!backupData || selected.length === 0) {
      return;
    }

    setImporting(true);
    try {
      const report = await importMutation.mutateAsync({
        data: backupData,
        collections: selected,
      });

      const restoredCount = report?.restored?.length || 0;
      const errorCount = Object.keys(report?.errors || {}).length;
      const message =
        errorCount > 0
          ? `Restored ${restoredCount} collection(s) with ${errorCount} error(s).`
          : `Successfully restored ${restoredCount} collection(s).`;

      showAlert(errorCount > 0 ? "warning" : "success", message);
      logInfo("Backup restored", {
        restored: restoredCount,
        errors: errorCount,
      });

      setBackupData(null);
      setFileName("");
      setSelected([]);
    } catch (error) {
      showAlert("error", error instanceof Error ? error.message : "Restore failed.");
      logError("Backup restore failed", error);
    } finally {
      setImporting(false);
    }
  };

  const outlinedButtonSx = {
    borderColor: `${themeColors.primary.main}80`,
    color: themeColors.primary.light,
    backdropFilter: "blur(8px)",
    transition: TRANSITIONS.cubic,
    "&:hover": {
      borderColor: themeColors.primary.main,
      background: `${themeColors.primary.main}15`,
      boxShadow: `0 0 25px ${themeColors.primary.main}30`,
    },
  };

  /** @type {React.ReactNode[] | null} */
  const restoreCollectionOptions = backupData
    ? ALL_COLLECTIONS.map((name) => {
        const available = backupData.collections[name] != null;
        const checked = selected.includes(name);
        return (
          <FormControlLabel
            key={name}
            disabled={!available}
            control={
              <Checkbox checked={checked} onChange={() => toggleCollection(name)} size="small" />
            }
            label={
              <Typography variant="body2" sx={{ textTransform: "capitalize" }}>
                {name.replace("_", " ")}
              </Typography>
            }
            sx={{
              m: 0,
              px: 1.5,
              py: 0.5,
              borderRadius: "8px",
              background: themeColors.alpha.card,
              border: `1px solid ${checked ? `${themeColors.primary.main}60` : "transparent"}`,
              transition: TRANSITIONS.cubic,
            }}
          />
        );
      })
    : null;

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Upload a backup file and choose which collections to restore.
      </Typography>

      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileChange}
        style={{ display: "none" }}
      />

      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={() => fileInputRef.current?.click()}
          startIcon={<IconFolderOpen size={16} />}
          sx={{ ...outlinedButtonSx, whiteSpace: "nowrap" }}
        >
          Choose File
        </Button>
        {fileName ? (
          <Box
            sx={{
              flex: 1,
              minWidth: 0,
              px: 2,
              py: 1,
              borderRadius: "10px",
              background: themeColors.alpha.card,
              border: `1px solid ${themeColors.alpha.cardBorder}`,
              backdropFilter: "blur(8px)",
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            <IconFile size={16} color={themeColors.primary.light} style={{ flexShrink: 0 }} />
            <Typography
              variant="body2"
              color="text.primary"
              sx={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {fileName}
            </Typography>
          </Box>
        ) : null}
      </Box>

      {backupData ? (
        <>
          <Chip
            icon={<IconClock size={14} />}
            label={`Exported ${new Date(backupData["exported_at"]).toLocaleString()}`}
            size="small"
            variant="outlined"
            sx={{
              mb: 2,
              borderColor: `${COMMON_COLORS.info.main}60`,
              color: COMMON_COLORS.info.light,
            }}
          />

          <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mb: 2.5 }}>
            {restoreCollectionOptions}
          </Stack>

          <Button
            variant="contained"
            disabled={importing || selected.length === 0}
            onClick={handleRestore}
            startIcon={
              importing ? (
                <CircularProgress size={18} color="inherit" />
              ) : (
                <IconDatabaseImport size={18} />
              )
            }
            sx={{
              background: `linear-gradient(135deg, ${COMMON_COLORS.warning.main} 0%, ${COMMON_COLORS.warning.dark} 100%)`,
              color: "#0f172a",
              fontWeight: 600,
              boxShadow: GLOW.subtle("#FBBF24"),
              transition: TRANSITIONS.cubic,
              "&:hover": {
                background: `linear-gradient(135deg, ${COMMON_COLORS.warning.light}CC 0%, ${COMMON_COLORS.warning.main}CC 100%)`,
                boxShadow: GLOW.medium("#FBBF24"),
                transform: "translateY(-2px)",
              },
            }}
          >
            {importing ? "Restoring..." : `Restore ${selected.length} Collection(s)`}
          </Button>
        </>
      ) : null}
    </Box>
  );
}

function MaintenanceSection() {
  const { themeColors } = useThemeContext();
  const { useActionData } = DataLoader();
  const mongoMigrationMutation = useActionData("maintenance/mongo-migration");
  const cleanupMutation = useActionData("maintenance/local-cleanup");

  const mutations = {
    "mongo-migration": mongoMigrationMutation,
    "local-cleanup": cleanupMutation,
  };

  // Toast firing is handled globally by MutationToastWatcher mounted at app
  // root, so the notification still appears if the user navigates away from
  // this page while the request is in flight.

  const handleRun = (task) => {
    // Fire-and-forget; MutationToastWatcher at app root surfaces the toast.
    mutations[task.key].mutate({});
  };

  const warningOutlinedSx = {
    borderColor: `${COMMON_COLORS.warning.main}80`,
    color: COMMON_COLORS.warning.light,
    transition: TRANSITIONS.cubic,
    "&:hover": {
      borderColor: COMMON_COLORS.warning.main,
      background: `${COMMON_COLORS.warning.main}15`,
      boxShadow: `0 0 25px ${COMMON_COLORS.warning.main}30`,
    },
  };

  return (
    <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
      {MAINTENANCE_TASKS.map((task) => {
        const TaskIcon = task.icon;
        const isPending = mutations[task.key].isPending;
        return (
          <Box
            key={task.key}
            component={motion.div}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            sx={{
              flex: 1,
              p: 2.5,
              borderRadius: "12px",
              background: themeColors.alpha.card,
              border: `1px solid ${themeColors.alpha.cardBorder}`,
              backdropFilter: "blur(8px)",
              transition: TRANSITIONS.cubic,
              display: "flex",
              flexDirection: "column",
              gap: 1,
              "&:hover": {
                borderColor: `${COMMON_COLORS.warning.main}60`,
                background: `${COMMON_COLORS.warning.main}08`,
                boxShadow: GLOW.subtle(COMMON_COLORS.warning.main),
              },
            }}
          >
            <TaskIcon size={28} color={COMMON_COLORS.warning.light} />
            <Typography variant="subtitle2" fontWeight={600}>
              {task.title}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
              {task.description}
            </Typography>
            <Box>
              <Button
                size="small"
                variant="outlined"
                disabled={isPending}
                onClick={() => handleRun(task)}
                startIcon={isPending ? <CircularProgress size={14} color="inherit" /> : null}
                sx={warningOutlinedSx}
              >
                {isPending ? "Running..." : "Run"}
              </Button>
            </Box>
          </Box>
        );
      })}
    </Stack>
  );
}

export default function Backup() {
  const { useRouteData } = DataLoader();
  const { data: summary, isLoading: isSummaryLoading } = useRouteData("backup/summary");

  // App-level snackbar lives in NotificationProvider so toasts survive page
  // navigation (e.g. a migration that completes while the user is elsewhere).
  const { showAlert } = useNotification();

  if (isSummaryLoading && !summary) {
    return <BackupSkeleton />;
  }

  return (
    <div className="space-y-6">
      <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible">
        <SectionCard
          title="Data Summary"
          icon={<IconInfoCircle size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <DataSummary summary={summary} />
        </SectionCard>
      </motion.div>

      <motion.div custom={1} variants={cardVariants} initial="hidden" animate="visible">
        <SectionCard
          title="Export"
          icon={<IconDatabaseExport size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <ExportSection showAlert={showAlert} />
        </SectionCard>
      </motion.div>

      <motion.div custom={2} variants={cardVariants} initial="hidden" animate="visible">
        <SectionCard
          title="Restore"
          icon={<IconDatabaseImport size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <RestoreSection showAlert={showAlert} />
        </SectionCard>
      </motion.div>

      <motion.div custom={3} variants={cardVariants} initial="hidden" animate="visible">
        <SectionCard
          title="Maintenance"
          icon={<IconTool size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <MaintenanceSection />
        </SectionCard>
      </motion.div>
    </div>
  );
}
