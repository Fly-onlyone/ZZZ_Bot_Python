import React, { useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Collapse,
  Dialog,
  DialogContent,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Pagination,
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
import DeleteSweepIcon from "@mui/icons-material/DeleteSweep";
import TrackChangesIcon from "@mui/icons-material/TrackChanges";
import DescriptionIcon from "@mui/icons-material/Description";
import GridViewIcon from "@mui/icons-material/GridView";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { DataLoader } from "../services";
import { BACKEND_URL } from "../config";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";
import { EmptyState } from "../components";

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

const HEADER_CELL_SX = { color: COMMON_COLORS.text.muted, fontWeight: 700 };
const DETAIL_COL_SPAN = 7;
const LOCATOR_PAGE_SIZE = 25;
const FAILURE_HISTORY_LIMIT = 50;
const CHILD_SCAN_PREVIEW_COUNT = 24;

function formatCaptureMode(mode) {
  if (mode === "failure") return "Failure Capture";
  if (mode === "recovery") return "Recovery Capture";
  return "No Capture";
}

function captureModeChipSx(mode) {
  if (mode === "failure") {
    return {
      backgroundColor: "rgba(244, 67, 54, 0.12)",
      color: "#ef5350",
    };
  }
  if (mode === "recovery") {
    return {
      backgroundColor: "rgba(255, 193, 7, 0.14)",
      color: "#ffca28",
    };
  }
  return {
    backgroundColor: "rgba(158, 158, 158, 0.12)",
    color: COMMON_COLORS.text.muted,
  };
}

function assetUrl(assetId) {
  if (!assetId) return null;
  const filename = assetId.replace("screenshot:", "");
  return `${BACKEND_URL}/assets/screenshot/${filename}`;
}

// ============================================================
// Expanded Detail Panel
// ============================================================

function DetailPanel({ entry, useRouteData, onOpenScreenshot, onOpenDom }) {
  const { themeColors } = useThemeContext();
  const isExpanded = true;
  const [showAllChildren, setShowAllChildren] = useState(false);

  const failureRoute = `locator-tracker/failures?limit=${FAILURE_HISTORY_LIMIT}&summary_id=${encodeURIComponent(
    entry.id,
  )}`;
  const { data: failures } = useRouteData(failureRoute, {
    queryKey: ["locator-tracker/failures", entry.id],
    enabled: isExpanded,
  });

  const childScanRoute = `locator-tracker/child-scan/${encodeURIComponent(entry.id)}`;
  const { data: childScanData } = useRouteData(childScanRoute, {
    queryKey: ["locator-tracker/child-scan", entry.id],
    enabled: isExpanded,
  });

  const failureRows = Array.isArray(failures) ? failures : [];
  const childScan = childScanData?.child_scan || [];
  const visibleChildScan = showAllChildren
    ? childScan
    : childScan.slice(0, CHILD_SCAN_PREVIEW_COUNT);

  return (
    <Box
      sx={{
        p: 2,
        display: "flex",
        flexDirection: "column",
        gap: 2,
        backdropFilter: "blur(8px)",
        transition: "all 0.3s ease-in-out",
        "&:hover": {
          boxShadow: `0 0 12px ${themeColors.glow}30`,
        },
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
        <Chip
          label={formatCaptureMode(entry.last_capture_mode)}
          size="small"
          sx={{
            ...captureModeChipSx(entry.last_capture_mode),
            fontWeight: 700,
            fontSize: "0.7rem",
          }}
        />
        {entry.last_success && entry.last_capture_mode === "recovery" && (
          <Typography variant="caption" sx={{ color: COMMON_COLORS.text.muted }}>
            Latest success followed an earlier failure, so recovery evidence was saved.
          </Typography>
        )}
      </Box>

      {/* Screenshots */}
      {(entry.page_asset_id || entry.locator_asset_id || entry.dom_snapshot_asset_id) && (
        <Box>
          <Typography variant="subtitle2" sx={{ color: COMMON_COLORS.text.muted, mb: 1 }}>
            Screenshots
          </Typography>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
            {entry.page_asset_id && (
              <Tooltip title="Full page screenshot" arrow>
                <IconButton size="small" onClick={() => onOpenScreenshot(entry.page_asset_id)}>
                  <img
                    src={assetUrl(entry.page_asset_id)}
                    alt="Page"
                    loading="lazy"
                    decoding="async"
                    style={{
                      width: 80,
                      height: 60,
                      objectFit: "cover",
                      borderRadius: 4,
                    }}
                  />
                </IconButton>
              </Tooltip>
            )}
            {entry.locator_asset_id && (
              <Tooltip title="Element screenshot" arrow>
                <IconButton size="small" onClick={() => onOpenScreenshot(entry.locator_asset_id)}>
                  <img
                    src={assetUrl(entry.locator_asset_id)}
                    alt="Element"
                    loading="lazy"
                    decoding="async"
                    style={{
                      width: 80,
                      height: 60,
                      objectFit: "contain",
                      borderRadius: 4,
                    }}
                  />
                </IconButton>
              </Tooltip>
            )}
            {entry.dom_snapshot_asset_id && (
              <Tooltip title="DOM snapshot" arrow>
                <IconButton size="small" onClick={() => onOpenDom(entry.dom_snapshot_asset_id)}>
                  <DescriptionIcon sx={{ color: themeColors.primary.main, fontSize: 32 }} />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      )}

      {/* Failure History */}
      {failureRows.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ color: COMMON_COLORS.text.muted, mb: 1 }}>
            Failure History ({failureRows.length})
          </Typography>
          <Box
            sx={{
              maxHeight: 200,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
            }}
          >
            {failureRows.map((f) => (
              <Box
                key={f.id}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  backgroundColor: "rgba(244, 67, 54, 0.05)",
                }}
              >
                <Typography
                  variant="caption"
                  sx={{ minWidth: 60, color: COMMON_COLORS.text.muted }}
                >
                  {relativeTime(f.seen_at)}
                </Typography>
                <Chip
                  label={formatCaptureMode(f.capture_mode)}
                  size="small"
                  sx={{
                    ...captureModeChipSx(f.capture_mode),
                    fontWeight: 700,
                    fontSize: "0.65rem",
                    height: 20,
                  }}
                />
                <Tooltip title={f.error_message || "-"} arrow>
                  <Typography
                    variant="caption"
                    sx={{
                      flex: 1,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {truncateText(f.error_message || "-", 80)}
                  </Typography>
                </Tooltip>
                {f.page_asset_id && (
                  <Button size="small" onClick={() => onOpenScreenshot(f.page_asset_id)}>
                    Page
                  </Button>
                )}
                {f.locator_asset_id && (
                  <Button size="small" onClick={() => onOpenScreenshot(f.locator_asset_id)}>
                    Element
                  </Button>
                )}
                {f.dom_snapshot_asset_id && (
                  <Button size="small" onClick={() => onOpenDom(f.dom_snapshot_asset_id)}>
                    DOM
                  </Button>
                )}
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Child Scan Gallery */}
      {childScan.length > 0 && (
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
            <GridViewIcon sx={{ color: COMMON_COLORS.text.muted, fontSize: 18 }} />
            <Typography variant="subtitle2" sx={{ color: COMMON_COLORS.text.muted }}>
              Page Elements ({childScan.length})
            </Typography>
          </Box>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))",
              gap: 1,
              maxHeight: 320,
              overflowY: "auto",
            }}
          >
            {visibleChildScan.map((child, idx) => (
              <Tooltip
                key={child.asset_id || idx}
                title={`<${child.tag}> ${
                  child.class_name ? "." + child.class_name.split(" ")[0] : ""
                } ${child.text ? '"' + child.text + '"' : ""}`}
                arrow
              >
                <Box
                  onClick={() => onOpenScreenshot(child.asset_id)}
                  sx={{
                    cursor: "pointer",
                    borderRadius: 1,
                    overflow: "hidden",
                    border: "1px solid",
                    borderColor: "divider",
                    "&:hover": { borderColor: themeColors.primary.main },
                  }}
                >
                  <img
                    src={assetUrl(child.asset_id)}
                    alt={`${child.tag} element`}
                    loading="lazy"
                    decoding="async"
                    style={{
                      width: "100%",
                      height: 60,
                      objectFit: "contain",
                      display: "block",
                    }}
                  />
                </Box>
              </Tooltip>
            ))}
          </Box>
          {childScan.length > CHILD_SCAN_PREVIEW_COUNT && (
            <Button
              size="small"
              sx={{ mt: 1, alignSelf: "flex-start" }}
              onClick={() => setShowAllChildren((value) => !value)}
            >
              {showAllChildren ? "Show fewer elements" : `Show all ${childScan.length} elements`}
            </Button>
          )}
        </Box>
      )}

      {/* Empty detail state */}
      {!entry.page_asset_id &&
        !entry.locator_asset_id &&
        !entry.dom_snapshot_asset_id &&
        failureRows.length === 0 &&
        childScan.length === 0 && (
          <Typography variant="body2" sx={{ color: COMMON_COLORS.text.muted }}>
            No detail data available.
          </Typography>
        )}
    </Box>
  );
}

// ============================================================
// Main Component
// ============================================================

export default function LocatorTracker() {
  const { useRouteData, useActionData } = DataLoader();
  const { themeColors } = useThemeContext();
  const [handlerFilter, setHandlerFilter] = useState("");
  const [failuresOnly, setFailuresOnly] = useState(false);
  const [sortField, setSortField] = useState("last_seen");
  const [sortDir, setSortDir] = useState("desc");
  const [expandedId, setExpandedId] = useState("");
  const [screenshotDialog, setScreenshotDialog] = useState("");
  const [page, setPage] = useState(1);
  const {
    data: entries,
    error,
    isLoading,
  } = useRouteData("locator-tracker", {
    gcTime: 1000 * 60,
  });
  const clearMutation = useActionData("locator-tracker/clear");

  const entryRows = Array.isArray(entries) ? entries : [];

  const handlers = useMemo(() => {
    return [...new Set(entryRows.map((entry) => String(entry.handler || "")))]
      .filter(Boolean)
      .sort();
  }, [entryRows]);

  const filteredEntries = useMemo(() => {
    let result = entryRows;
    if (handlerFilter) result = result.filter((entry) => entry.handler === handlerFilter);
    if (failuresOnly) result = result.filter((entry) => entry.failure_count > 0);

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
  }, [entryRows, failuresOnly, handlerFilter, sortDir, sortField]);
  const pageCount = Math.ceil(filteredEntries.length / LOCATOR_PAGE_SIZE);
  const visibleEntries = useMemo(() => {
    const startIndex = (page - 1) * LOCATOR_PAGE_SIZE;
    return filteredEntries.slice(startIndex, startIndex + LOCATOR_PAGE_SIZE);
  }, [filteredEntries, page]);

  const handlerOptions = useMemo(
    () =>
      handlers.map((handler) => (
        <MenuItem key={handler} value={handler}>
          {handler}
        </MenuItem>
      )),
    [handlers],
  );

  const openScreenshot = (assetId) => {
    const url = assetUrl(assetId);
    if (url) setScreenshotDialog(url);
  };

  const openDom = (assetId) => {
    const url = assetUrl(assetId);
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir((direction) => (direction === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  };

  React.useEffect(() => {
    setPage(1);
    setExpandedId("");
  }, [failuresOnly, handlerFilter, sortDir, sortField]);

  React.useEffect(() => {
    if (expandedId && !visibleEntries.some((entry) => entry.id === expandedId)) {
      setExpandedId("");
    }
  }, [expandedId, visibleEntries]);

  if (error) {
    return (
      <Alert severity="error">
        Failed to load locator data: {error instanceof Error ? error.message : String(error)}
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

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap" }}>
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
            <TableHead
              sx={{
                "& .MuiTableCell-head": {
                  textShadow: `0 0 15px ${themeColors.glow}20`,
                },
              }}
            >
              <TableRow>
                <TableCell sx={HEADER_CELL_SX} padding="checkbox" />
                <TableCell sx={HEADER_CELL_SX}>Selector</TableCell>
                <TableCell sx={HEADER_CELL_SX}>Handler</TableCell>
                <TableCell sx={HEADER_CELL_SX}>Action</TableCell>
                <TableCell sx={HEADER_CELL_SX}>Status</TableCell>
                <TableCell sx={HEADER_CELL_SX}>
                  <TableSortLabel
                    active={sortField === "hit_count"}
                    direction={sortField === "hit_count" ? sortDir : "desc"}
                    onClick={() => handleSort("hit_count")}
                  >
                    Hits
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={HEADER_CELL_SX}>Last Error</TableCell>
                <TableCell sx={HEADER_CELL_SX}>
                  <TableSortLabel
                    active={sortField === "last_seen"}
                    direction={sortField === "last_seen" ? sortDir : "desc"}
                    onClick={() => handleSort("last_seen")}
                  >
                    Last Seen
                  </TableSortLabel>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {visibleEntries.map((entry) => {
                const isOpen = expandedId === entry.id;
                return (
                  <React.Fragment key={entry.id}>
                    <TableRow
                      onClick={() => setExpandedId((cur) => (cur === entry.id ? "" : entry.id))}
                      sx={{
                        cursor: "pointer",
                        backgroundColor: isOpen ? `${themeColors.primary.main}15` : "transparent",
                        "&:hover": {
                          backgroundColor: `${themeColors.primary.main}10`,
                        },
                      }}
                    >
                      <TableCell padding="checkbox">
                        <ExpandMoreIcon
                          sx={{
                            fontSize: 18,
                            color: COMMON_COLORS.text.muted,
                            transition: "transform 0.2s",
                            transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
                          }}
                        />
                      </TableCell>
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
                          sx={{
                            fontFamily: "monospace",
                            fontSize: "0.75rem",
                          }}
                        >
                          {entry.action}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 0.75,
                            flexWrap: "wrap",
                          }}
                        >
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
                          {entry.last_capture_mode && (
                            <Chip
                              label={
                                entry.last_capture_mode === "recovery" ? "RECOVERY" : "CAPTURED"
                              }
                              size="small"
                              sx={{
                                ...captureModeChipSx(entry.last_capture_mode),
                                fontWeight: 700,
                                fontSize: "0.65rem",
                              }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{entry.hit_count}</Typography>
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
                    </TableRow>

                    {/* Expandable detail row */}
                    <TableRow>
                      <TableCell
                        colSpan={DETAIL_COL_SPAN + 1}
                        sx={{
                          p: 0,
                          borderBottom: isOpen ? undefined : "none",
                        }}
                      >
                        <Collapse in={isOpen} timeout="auto" unmountOnExit>
                          <DetailPanel
                            entry={entry}
                            useRouteData={useRouteData}
                            onOpenScreenshot={openScreenshot}
                            onOpenDom={openDom}
                          />
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {pageCount > 1 && (
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <Pagination
            count={pageCount}
            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
            size="small"
          />
        </Box>
      )}

      <Dialog open={!!screenshotDialog} onClose={() => setScreenshotDialog(null)} maxWidth="lg">
        <DialogContent sx={{ p: 1 }}>
          {screenshotDialog ? (
            <img
              src={screenshotDialog}
              alt="Full screenshot"
              loading="lazy"
              decoding="async"
              style={{ maxWidth: "100%", maxHeight: "80vh" }}
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
