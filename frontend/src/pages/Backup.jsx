import React, { useEffect, useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  FormControlLabel,
  Snackbar,
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
  IconDatabaseExport,
  IconDatabaseImport,
  IconFolderOpen,
  IconInfoCircle,
} from "@tabler/icons-react";

import { BackupSkeleton, SectionCard } from "../components";
import { BACKEND_URL } from "../config";
import { DataLoader } from "../services";
import { logError, logInfo } from "../services/sentryLogger.js";
import { GLOW } from "../theme/styles";
import { COMMON_COLORS } from "../theme/colors";

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

const ALL_COLLECTIONS = [
  "settings",
  "account",
  "shopping",
  "redemptions",
  "missions",
  "last_run",
];

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
        <TableCell sx={{ textTransform: "capitalize" }}>
          {name.replace("_", " ")}
        </TableCell>
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
      // Auto-save the picked path
      await saveConfigMutation.mutateAsync({ export_path: result.path });
      showAlert("success", "Export folder set.");
      logInfo("Backup export path selected", { path: result.path });
    } catch (error) {
      showAlert(
        "error",
        error instanceof Error ? error.message : "Failed to open folder picker."
      );
    }
  };

  const handleExport = async () => {
    try {
      const result = await exportMutation.mutateAsync({});
      logInfo("Backup exported successfully", { file: result?.file });
      showAlert("success", `Backup saved to ${result?.file}`);
    } catch (error) {
      logError("Backup export failed", error);
      showAlert(
        "error",
        error instanceof Error ? error.message : "Export failed."
      );
    }
  };

  const pathEmpty = !exportPath.trim();

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Set the folder where backups will be saved, then export.
      </Typography>

      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={handleBrowse}
          startIcon={<IconFolderOpen size={16} />}
          sx={{ whiteSpace: "nowrap" }}
        >
          Choose Folder
        </Button>
        <Typography
          variant="body2"
          color={exportPath ? "text.primary" : "text.disabled"}
          sx={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {exportPath || "No folder selected"}
        </Typography>
      </Box>

      <Button
        variant="contained"
        disabled={
          pathEmpty || exportMutation.isPending || saveConfigMutation.isPending
        }
        onClick={handleExport}
        startIcon={<IconDatabaseExport size={18} />}
      >
        {exportMutation.isPending ? "Exporting..." : "Export Backup"}
      </Button>
    </Box>
  );
}

function RestoreSection({ showAlert }) {
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
        setSelected(
          ALL_COLLECTIONS.filter((c) => parsed.collections[c] != null)
        );
      } catch {
        showAlert("error", "Could not parse JSON file.");
        setBackupData(null);
      }
    };
    reader.readAsText(file);
    event.target.value = "";
  };

  const toggleCollection = (name) => {
    setSelected((prev) =>
      prev.includes(name) ? prev.filter((c) => c !== name) : [...prev, name]
    );
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
      showAlert(
        "error",
        error instanceof Error ? error.message : "Restore failed."
      );
      logError("Backup restore failed", error);
    } finally {
      setImporting(false);
    }
  };

  /** @type {React.ReactNode[] | null} */
  const restoreCollectionOptions = backupData
    ? ALL_COLLECTIONS.map((name) => {
        const available = backupData.collections[name] != null;
        return (
          <FormControlLabel
            key={name}
            disabled={!available}
            control={
              <Checkbox
                checked={selected.includes(name)}
                onChange={() => toggleCollection(name)}
                size="small"
              />
            }
            label={
              <Typography variant="body2" sx={{ textTransform: "capitalize" }}>
                {name.replace("_", " ")}
              </Typography>
            }
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
      <Button
        variant="outlined"
        onClick={() => fileInputRef.current?.click()}
        sx={{ mb: 2 }}
      >
        {fileName || "Choose Backup File"}
      </Button>

      {backupData ? (
        <>
          <Typography variant="body2" sx={{ mb: 1, mt: 1 }}>
            Exported at: {new Date(backupData["exported_at"]).toLocaleString()}
          </Typography>

          <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
            {restoreCollectionOptions}
          </Stack>

          <Button
            variant="contained"
            disabled={importing || selected.length === 0}
            onClick={handleRestore}
            startIcon={<IconDatabaseImport size={18} />}
            sx={{
              background: `linear-gradient(135deg, ${COMMON_COLORS.warning.main} 0%, ${COMMON_COLORS.warning.dark} 100%)`,
              color: "#0f172a",
              fontWeight: 600,
              boxShadow: GLOW.subtle("#FBBF24"),
              "&:hover": {
                background: `linear-gradient(135deg, ${COMMON_COLORS.warning.light}CC 0%, ${COMMON_COLORS.warning.main}CC 100%)`,
                boxShadow: GLOW.medium("#FBBF24"),
                transform: "translateY(-2px)",
              },
            }}
          >
            {importing
              ? "Restoring..."
              : `Restore ${selected.length} Collection(s)`}
          </Button>
        </>
      ) : null}
    </Box>
  );
}

export default function Backup() {
  /**
   * @typedef {{
   *   open: boolean,
   *   type: import("@mui/material").AlertColor,
   *   message: string,
   * }} BackupAlertState
   */

  const { useRouteData } = DataLoader();
  const { data: summary, isLoading: isSummaryLoading } =
    useRouteData("backup/summary");

  /** @type {[BackupAlertState, React.Dispatch<React.SetStateAction<BackupAlertState>>]} */
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });

  const showAlert = (type, message) => setAlert({ open: true, type, message });
  const handleAlertClose = () => setAlert({ ...alert, open: false });

  if (isSummaryLoading && !summary) {
    return <BackupSkeleton />;
  }

  return (
    <div className="space-y-6">
      <motion.div
        custom={0}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <SectionCard
          title="Data Summary"
          icon={<IconInfoCircle size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <DataSummary summary={summary} />
        </SectionCard>
      </motion.div>

      <motion.div
        custom={1}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <SectionCard
          title="Export"
          icon={<IconDatabaseExport size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <ExportSection showAlert={showAlert} />
        </SectionCard>
      </motion.div>

      <motion.div
        custom={2}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <SectionCard
          title="Restore"
          icon={<IconDatabaseImport size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <RestoreSection showAlert={showAlert} />
        </SectionCard>
      </motion.div>

      <Snackbar
        open={alert.open}
        autoHideDuration={5000}
        onClose={handleAlertClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={alert.type}>{alert.message}</Alert>
      </Snackbar>
    </div>
  );
}
