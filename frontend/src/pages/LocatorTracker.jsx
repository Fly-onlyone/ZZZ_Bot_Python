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
import DescriptionIcon from "@mui/icons-material/Description";
import { DataLoader } from "../services";
import { BACKEND_URL } from "../config";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";
import { EmptyState } from "../components";

/**
 * @typedef {Object} LocatorSummary
 * @property {string} id
 * @property {string} selector
 * @property {string} handler
 * @property {string} action
 * @property {boolean} last_success
 * @property {string | null | undefined} last_error
 * @property {number} hit_count
 * @property {number} success_count
 * @property {number} failure_count
 * @property {string | null | undefined} last_seen
 * @property {string | null | undefined} page_asset_id
 * @property {string | null | undefined} locator_asset_id
 * @property {string | null | undefined} dom_snapshot_asset_id
 */

/**
 * @typedef {Object} LocatorFailure
 * @property {string} id
 * @property {string} summary_id
 * @property {string} selector
 * @property {string} handler
 * @property {string} action
 * @property {string | null | undefined} error_message
 * @property {string | null | undefined} seen_at
 * @property {string | null | undefined} page_asset_id
 * @property {string | null | undefined} locator_asset_id
 * @property {string | null | undefined} dom_snapshot_asset_id
 */

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

function truncateText(value, maxLen = 36) {
  if (!value || value.length <= maxLen) return value;
  return value.slice(0, maxLen) + "\u2026";
}

export default function LocatorTracker() {
  const { useRouteData, useActionData } = DataLoader();
  const { themeColors } = useThemeContext();
  const [handlerFilter, setHandlerFilter] = useState("");
  const [failuresOnly, setFailuresOnly] = useState(false);
  const [sortField, setSortField] = useState("last_seen");
  const [sortDir, setSortDir] = useState("desc");
  const [selectedSummaryId, setSelectedSummaryId] = useState("");
  const [screenshotDialog, setScreenshotDialog] = useState("");
  const { data: entries, error, isLoading } = useRouteData("locator-tracker");
  const failureRoute = useMemo(() => {
    const params = new URLSearchParams({
      limit: selectedSummaryId ? "500" : "100",
    });
    if (selectedSummaryId) {
      params.set("summary_id", selectedSummaryId);
    }
    return `locator-tracker/failures?${params.toString()}`;
  }, [selectedSummaryId]);
  const {
    data: failures,
    error: failuresError,
    isLoading: failuresLoading,
  } = useRouteData(failureRoute, {
    queryKey: ["locator-tracker/failures", selectedSummaryId || ""],
  });
  const clearMutation = useActionData("locator-tracker/clear");

  const entryRows = /** @type {LocatorSummary[]} */ (
    Array.isArray(entries) ? entries : []
  );
  const failureRows = /** @type {LocatorFailure[]} */ (
    Array.isArray(failures) ? failures : []
  );

  const handlers = /** @type {string[]} */ (
    useMemo(() => {
      return [...new Set(entryRows.map((entry) => String(entry.handler || "")))]
        .filter(Boolean)
        .sort();
    }, [entryRows])
  );

  const filteredEntries = /** @type {LocatorSummary[]} */ (
    useMemo(() => {
      let result = entryRows;
      if (handlerFilter)
        result = result.filter((entry) => entry.handler === handlerFilter);
      if (failuresOnly)
        result = result.filter((entry) => entry.failure_count > 0);

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
    }, [entryRows, failuresOnly, handlerFilter, sortDir, sortField])
  );

  const filteredFailures = /** @type {LocatorFailure[]} */ (
    useMemo(() => {
      let result = failureRows;
      if (handlerFilter)
        result = result.filter((entry) => entry.handler === handlerFilter);
      return result;
    }, [failureRows, handlerFilter])
  );

  const handlerOptions = /** @type {JSX.Element[]} */ (
    useMemo(
      () =>
        handlers.map((handler) => (
          <MenuItem key={handler} value={handler}>
            {handler}
          </MenuItem>
        )),
      [handlers]
    )
  );

  const assetUrl = (assetId) => {
    if (!assetId) return null;
    const filename = assetId.replace("screenshot:", "");
    return `${BACKEND_URL}/assets/screenshot/${filename}`;
  };

  const openAsset = (assetId, type = "image") => {
    const url = assetUrl(assetId);
    if (!url) return;
    if (type === "dom") {
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }
    setScreenshotDialog(url);
  };

  const entryTableRows = /** @type {JSX.Element[]} */ (
    useMemo(
      () =>
        filteredEntries.map((entry) => (
          <TableRow
            key={entry.id}
            component={motion.tr}
            variants={itemVariants}
            onClick={() =>
              setSelectedSummaryId((current) =>
                current === entry.id ? "" : entry.id
              )
            }
            sx={{
              cursor: "pointer",
              backgroundColor:
                selectedSummaryId === entry.id
                  ? `${themeColors.primary.main}15`
                  : "transparent",
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
                  {truncateText(entry.selector)}
                </Typography>
              </Tooltip>
            </TableCell>
            <TableCell>
              <Typography variant="body2">{entry.handler}</Typography>
            </TableCell>
            <TableCell>
              <Typography
                variant="body2"
                sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
              >
                {entry.action}
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
              <Typography
                variant="body2"
                sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
              >
                {entry.success_count}/{entry.failure_count}
              </Typography>
            </TableCell>
            <TableCell>
              <Tooltip title={entry.last_error || "-"} arrow>
                <Typography
                  variant="body2"
                  sx={{
                    maxWidth: 220,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {truncateText(entry.last_error || "-", 48)}
                </Typography>
              </Tooltip>
            </TableCell>
            <TableCell>
              <Tooltip title={entry.last_seen || "-"} arrow>
                <Typography variant="body2" sx={{ fontSize: "0.75rem" }}>
                  {relativeTime(entry.last_seen)}
                </Typography>
              </Tooltip>
            </TableCell>
            <TableCell>
              {entry.page_asset_id ? (
                <IconButton
                  size="small"
                  onClick={() => openAsset(entry.page_asset_id)}
                >
                  <img
                    src={assetUrl(entry.page_asset_id)}
                    alt="Page"
                    style={{
                      width: 48,
                      height: 48,
                      objectFit: "cover",
                      borderRadius: 4,
                    }}
                  />
                </IconButton>
              ) : (
                <ImageIcon
                  sx={{
                    color: COMMON_COLORS.text.muted,
                    opacity: 0.3,
                    fontSize: 20,
                  }}
                />
              )}
            </TableCell>
            <TableCell>
              {entry.locator_asset_id ? (
                <IconButton
                  size="small"
                  onClick={() => openAsset(entry.locator_asset_id)}
                >
                  <img
                    src={assetUrl(entry.locator_asset_id)}
                    alt="Element"
                    style={{
                      width: 48,
                      height: 48,
                      objectFit: "contain",
                      borderRadius: 4,
                    }}
                  />
                </IconButton>
              ) : (
                <ImageIcon
                  sx={{
                    color: COMMON_COLORS.text.muted,
                    opacity: 0.3,
                    fontSize: 20,
                  }}
                />
              )}
            </TableCell>
            <TableCell>
              {entry.dom_snapshot_asset_id ? (
                <IconButton
                  size="small"
                  onClick={() => openAsset(entry.dom_snapshot_asset_id, "dom")}
                >
                  <DescriptionIcon sx={{ color: themeColors.primary.main }} />
                </IconButton>
              ) : (
                <DescriptionIcon
                  sx={{
                    color: COMMON_COLORS.text.muted,
                    opacity: 0.3,
                    fontSize: 20,
                  }}
                />
              )}
            </TableCell>
          </TableRow>
        )),
      [filteredEntries, selectedSummaryId, themeColors.primary.main]
    )
  );

  const failureTableRows = /** @type {JSX.Element[]} */ (
    useMemo(
      () =>
        filteredFailures.map((failure) => (
          <TableRow key={failure.id}>
            <TableCell>
              <Tooltip title={failure.seen_at || "-"} arrow>
                <Typography variant="body2" sx={{ fontSize: "0.75rem" }}>
                  {relativeTime(failure.seen_at)}
                </Typography>
              </Tooltip>
            </TableCell>
            <TableCell>
              <Typography variant="body2">{failure.handler}</Typography>
            </TableCell>
            <TableCell>
              <Typography
                variant="body2"
                sx={{ fontFamily: "monospace", fontSize: "0.75rem" }}
              >
                {failure.action}
              </Typography>
            </TableCell>
            <TableCell>
              <Tooltip title={failure.selector} arrow>
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
                  {truncateText(failure.selector)}
                </Typography>
              </Tooltip>
            </TableCell>
            <TableCell>
              <Tooltip title={failure.error_message || "-"} arrow>
                <Typography
                  variant="body2"
                  sx={{
                    maxWidth: 280,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {truncateText(failure.error_message || "-", 64)}
                </Typography>
              </Tooltip>
            </TableCell>
            <TableCell>
              {failure.page_asset_id ? (
                <Button
                  size="small"
                  onClick={() => openAsset(failure.page_asset_id)}
                >
                  Page
                </Button>
              ) : (
                "-"
              )}
            </TableCell>
            <TableCell>
              {failure.locator_asset_id ? (
                <Button
                  size="small"
                  onClick={() => openAsset(failure.locator_asset_id)}
                >
                  Element
                </Button>
              ) : (
                "-"
              )}
            </TableCell>
            <TableCell>
              {failure.dom_snapshot_asset_id ? (
                <Button
                  size="small"
                  onClick={() =>
                    openAsset(failure.dom_snapshot_asset_id, "dom")
                  }
                >
                  DOM
                </Button>
              ) : (
                "-"
              )}
            </TableCell>
          </TableRow>
        )),
      [filteredFailures]
    )
  );

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir((direction) => (direction === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  const loadError = error || failuresError;
  const loadErrorMessage = loadError
    ? loadError instanceof Error
      ? loadError.message
      : String(loadError)
    : "";

  if (loadError) {
    return (
      <Alert severity="error">
        Failed to load locator data: {loadErrorMessage}
      </Alert>
    );
  }

  if (isLoading || failuresLoading || !entries || !failures) {
    return (
      <Typography
        sx={{ color: COMMON_COLORS.text.muted, textAlign: "center", mt: 4 }}
      >
        Loading locator data...
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Box
        sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap" }}
      >
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Handler</InputLabel>
          <Select
            value={handlerFilter}
            label="Handler"
            variant="outlined"
            onChange={(event) => setHandlerFilter(event.target.value)}
          >
            <MenuItem value="">All</MenuItem>
            {handlerOptions}
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={failuresOnly}
              onChange={(event) => setFailuresOnly(event.target.checked)}
              size="small"
            />
          }
          label="Failures only"
          sx={{ color: COMMON_COLORS.text.muted }}
        />

        {selectedSummaryId ? (
          <Button
            size="small"
            variant="text"
            onClick={() => setSelectedSummaryId("")}
          >
            Clear failure filter
          </Button>
        ) : null}

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

      {filteredEntries.length === 0 ? (
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
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Selector
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Handler
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Action
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Status
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  <TableSortLabel
                    active={sortField === "hit_count"}
                    direction={sortField === "hit_count" ? sortDir : "desc"}
                    onClick={() => handleSort("hit_count")}
                  >
                    Hits
                  </TableSortLabel>
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Success/Fail
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Last Error
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  <TableSortLabel
                    active={sortField === "last_seen"}
                    direction={sortField === "last_seen" ? sortDir : "desc"}
                    onClick={() => handleSort("last_seen")}
                  >
                    Last Seen
                  </TableSortLabel>
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Page
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Element
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  DOM
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody
              component={motion.tbody}
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              <AnimatePresence>{entryTableRows}</AnimatePresence>
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          Recent Failures
        </Typography>
        {selectedSummaryId ? (
          <Chip
            size="small"
            label="Filtered to selected summary"
            sx={{
              backgroundColor: `${themeColors.primary.main}20`,
              color: themeColors.primary.main,
            }}
          />
        ) : null}
      </Box>

      {filteredFailures.length === 0 ? (
        <Paper
          sx={{
            p: 3,
            backgroundColor: "transparent",
            backgroundImage: "none",
            boxShadow: "none",
          }}
        >
          <Typography sx={{ color: COMMON_COLORS.text.muted }}>
            No failure events available.
          </Typography>
        </Paper>
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
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  When
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Handler
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Action
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Selector
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Error
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Page
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  Element
                </TableCell>
                <TableCell
                  sx={{ color: COMMON_COLORS.text.muted, fontWeight: 700 }}
                >
                  DOM
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>{failureTableRows}</TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog
        open={!!screenshotDialog}
        onClose={() => setScreenshotDialog(null)}
        maxWidth="lg"
      >
        <DialogContent sx={{ p: 1 }}>
          {screenshotDialog ? (
            <img
              src={screenshotDialog}
              alt="Full screenshot"
              style={{ maxWidth: "100%", maxHeight: "80vh" }}
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
