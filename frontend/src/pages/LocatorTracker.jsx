import React, { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip,
  Typography,
} from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import DeleteSweepIcon from "@mui/icons-material/DeleteSweep";
import ImageIcon from "@mui/icons-material/Image";
import TrackChangesIcon from "@mui/icons-material/TrackChanges";
import { DataLoader, BACKEND_URL } from "../services/DataLoader";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";
import { EmptyState } from "../components";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.04, when: "beforeChildren" },
  },
};

const itemVariants = {
  hidden: { opacity: 0, x: -15 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { type: "spring", stiffness: 120, damping: 18 },
  },
};

function relativeTime(dateStr) {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
}

function truncateSelector(selector, maxLen = 36) {
  if (!selector || selector.length <= maxLen) return selector;
  return selector.slice(0, maxLen) + "\u2026";
}

export default function LocatorTracker() {
  const { useRouteData, useActionData } = DataLoader();
  const { themeColors } = useThemeContext();
  const { data: entries, error, isLoading } = useRouteData("locator-tracker");
  const clearMutation = useActionData("locator-tracker/clear");

  const [handlerFilter, setHandlerFilter] = useState("");
  const [failuresOnly, setFailuresOnly] = useState(false);
  const [sortField, setSortField] = useState("last_seen");
  const [sortDir, setSortDir] = useState("desc");
  const [screenshotDialog, setScreenshotDialog] = useState(null);

  const handlers = useMemo(() => {
    if (!Array.isArray(entries)) return [];
    return [...new Set(entries.map((e) => e.handler))].sort();
  }, [entries]);

  const filtered = useMemo(() => {
    if (!Array.isArray(entries)) return [];
    let result = entries;
    if (handlerFilter) result = result.filter((e) => e.handler === handlerFilter);
    if (failuresOnly) result = result.filter((e) => e.failure_count > 0);

    result = [...result].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      if (typeof aVal === "string") aVal = aVal.toLowerCase();
      if (typeof bVal === "string") bVal = bVal.toLowerCase();
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return result;
  }, [entries, handlerFilter, failuresOnly, sortField, sortDir]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  if (error) {
    return (
      <Alert severity="error">
        Failed to load locator data: {error.message}
      </Alert>
    );
  }

  if (isLoading || !entries) {
    return (
      <Typography sx={{ color: COMMON_COLORS.text.muted, textAlign: "center", mt: 4 }}>
        Loading locator data...
      </Typography>
    );
  }

  const screenshotUrl = (assetId) => {
    if (!assetId) return null;
    const filename = assetId.replace("screenshot:", "");
    return `${BACKEND_URL}/assets/screenshot/${filename}`;
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {/* Toolbar */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Handler</InputLabel>
          <Select
            value={handlerFilter}
            label="Handler"
            onChange={(e) => setHandlerFilter(e.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            {handlers.map((h) => (
              <MenuItem key={h} value={h}>
                {h}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={failuresOnly}
              onChange={(e) => setFailuresOnly(e.target.checked)}
              size="small"
            />
          }
          label="Failures only"
          sx={{ color: COMMON_COLORS.text.muted }}
        />

        <Box sx={{ flex: 1 }} />

        <Button
          variant="outlined"
          color="error"
          size="small"
          startIcon={<DeleteSweepIcon />}
          onClick={() => clearMutation.mutateAsync({})}
          disabled={clearMutation.isPending}
        >
          Clear All
        </Button>
      </Box>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<TrackChangesIcon sx={{ fontSize: 48 }} />}
          message="No locator data recorded yet"
        />
      ) : (
        <TableContainer
          component={Paper}
          sx={{
            backgroundColor: "transparent",
            backgroundImage: "none",
            boxShadow: "none",
          }}
        >
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  Selector
                </TableCell>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  Handler
                </TableCell>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  Action
                </TableCell>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  Status
                </TableCell>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  <TableSortLabel
                    active={sortField === "hit_count"}
                    direction={sortField === "hit_count" ? sortDir : "desc"}
                    onClick={() => handleSort("hit_count")}
                  >
                    Hits
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  Success/Fail
                </TableCell>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  <TableSortLabel
                    active={sortField === "last_seen"}
                    direction={sortField === "last_seen" ? sortDir : "desc"}
                    onClick={() => handleSort("last_seen")}
                  >
                    Last Seen
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}>
                  Screenshot
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody
              component={motion.tbody}
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              <AnimatePresence>
                {filtered.map((entry) => (
                  <TableRow
                    key={entry.id}
                    component={motion.tr}
                    variants={itemVariants}
                    sx={{
                      "&:hover": {
                        backgroundColor: `${themeColors.primary.main}10`,
                      },
                    }}
                  >
                    <TableCell>
                      <Tooltip title={entry.selector} arrow>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: "monospace",
                            fontSize: "0.75rem",
                            maxWidth: 220,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {truncateSelector(entry.selector)}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{entry.handler}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                        {entry.last_action}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={entry.last_success ? "OK" : "FAIL"}
                        size="small"
                        sx={{
                          backgroundColor: entry.last_success
                            ? "rgba(76, 175, 80, 0.15)"
                            : "rgba(244, 67, 54, 0.15)",
                          color: entry.last_success ? "#66bb6a" : "#ef5350",
                          fontWeight: 700,
                          fontSize: "0.7rem",
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{entry.hit_count}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}>
                        {entry.success_count}/{entry.failure_count}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Tooltip title={entry.last_seen || "-"} arrow>
                        <Typography variant="body2" sx={{ fontSize: "0.75rem" }}>
                          {relativeTime(entry.last_seen)}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      {entry.screenshot_asset_id ? (
                        <IconButton
                          size="small"
                          onClick={() =>
                            setScreenshotDialog(
                              screenshotUrl(entry.screenshot_asset_id)
                            )
                          }
                        >
                          <img
                            src={screenshotUrl(entry.screenshot_asset_id)}
                            alt="Screenshot"
                            style={{
                              width: 48,
                              height: 48,
                              objectFit: "cover",
                              borderRadius: 4,
                            }}
                          />
                        </IconButton>
                      ) : (
                        <ImageIcon sx={{ color: COMMON_COLORS.text.muted, opacity: 0.3, fontSize: 20 }} />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </AnimatePresence>
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Screenshot full-size dialog */}
      <Dialog
        open={!!screenshotDialog}
        onClose={() => setScreenshotDialog(null)}
        maxWidth="lg"
      >
        <DialogContent sx={{ p: 1 }}>
          {screenshotDialog && (
            <img
              src={screenshotDialog}
              alt="Full screenshot"
              style={{ maxWidth: "100%", maxHeight: "80vh" }}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
