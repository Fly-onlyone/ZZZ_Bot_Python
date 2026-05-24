import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Box,
  Chip,
  FormControl,
  FormControlLabel,
  IconButton,
  InputAdornment,
  MenuItem,
  Pagination,
  Select,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import ArticleIcon from "@mui/icons-material/Article";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
import SectionCard from "../components/common/SectionCard.jsx";
import { LogsSkeleton } from "../components";
import { BACKEND_URL } from "../config";
import { COMMON_COLORS } from "../theme/colors.js";
import { useThemeContext } from "../theme/ThemeContext.jsx";

// ============================================================================
// Constants
// ============================================================================

const LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"];

const LEVEL_COLORS = {
  DEBUG: "#94a3b8",
  INFO: "#22d3ee",
  WARNING: "#fbbf24",
  ERROR: "#f87171",
  CRITICAL: "#fca5a5",
};

const DEFAULT_PAGE_SIZE = 50;

// ============================================================================
// Data fetcher
// ============================================================================

async function fetchLogs({ date, levels, search, page }) {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  if (levels.length > 0 && levels.length < LEVELS.length) params.set("level", levels.join(","));
  if (search) params.set("search", search);
  params.set("limit", String(DEFAULT_PAGE_SIZE));
  params.set("offset", String((page - 1) * DEFAULT_PAGE_SIZE));

  const res = await fetch(`${BACKEND_URL}/logs?${params}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ============================================================================
// Logs Page
// ============================================================================

export default function Logs() {
  const { themeColors } = useThemeContext();

  // Filter state
  const [selectedFile, setSelectedFile] = useState("");
  const [selectedLevels, setSelectedLevels] = useState([...LEVELS]);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const debounceRef = useRef(null);

  // Debounce search input (300 ms)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(debounceRef.current);
  }, [search]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [selectedFile, selectedLevels, debouncedSearch]);

  const { data, error, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["logs", selectedFile, selectedLevels.join(","), debouncedSearch, page],
    queryFn: () =>
      fetchLogs({
        date: selectedFile || null,
        levels: selectedLevels,
        search: debouncedSearch,
        page,
      }),
    refetchInterval: autoRefresh ? 5000 : false,
    staleTime: 0,
    gcTime: 1000 * 60,
  });

  const files = data?.files ?? [];
  const entries = data?.entries ?? [];
  const total = data?.total ?? 0;
  const pageCount = Math.ceil(total / DEFAULT_PAGE_SIZE);

  // Per-level counts for the stats row (computed from current page entries)
  const levelCounts = useMemo(() => {
    const counts = Object.fromEntries(LEVELS.map((level) => [level, 0]));
    for (const entry of entries) {
      if (counts[entry.level] !== undefined) {
        counts[entry.level] += 1;
      }
    }
    return counts;
  }, [entries]);

  if (isLoading && !data) {
    return <LogsSkeleton />;
  }

  const toggleLevel = (lvl) =>
    setSelectedLevels((prev) =>
      prev.includes(lvl) ? prev.filter((l) => l !== lvl) : [...prev, lvl]
    );
  const errorMessage = error instanceof Error ? error.message : String(error);
  /** @type {React.ReactNode[]} */
  const fileOptions = files
    .filter((f) => f !== "app.log")
    .map((f) => (
      <MenuItem key={f} value={f.replace("app.log.", "")}>
        {f}
      </MenuItem>
    ));
  /** @type {React.ReactNode[]} */
  const levelFilterChips = LEVELS.map((lvl) => {
    const active = selectedLevels.includes(lvl);
    return (
      <Chip
        key={lvl}
        label={lvl}
        size="small"
        onClick={() => toggleLevel(lvl)}
        sx={{
          backgroundColor: active ? `${LEVEL_COLORS[lvl]}33` : "transparent",
          color: active ? LEVEL_COLORS[lvl] : COMMON_COLORS.text.muted,
          border: `1px solid ${active ? LEVEL_COLORS[lvl] : COMMON_COLORS.text.muted}66`,
          fontWeight: 600,
          fontSize: "0.7rem",
          cursor: "pointer",
          transition: "all 0.2s",
          "&:hover": {
            backgroundColor: `${LEVEL_COLORS[lvl]}22`,
            border: `1px solid ${LEVEL_COLORS[lvl]}`,
          },
        }}
      />
    );
  });
  /** @type {React.ReactNode[]} */
  const levelSummaryChips = LEVELS.map((lvl) => (
    <Chip
      key={lvl}
      label={`${lvl}: ${levelCounts[lvl]}`}
      size="small"
      sx={{
        backgroundColor: `${LEVEL_COLORS[lvl]}1A`,
        color: LEVEL_COLORS[lvl],
        border: `1px solid ${LEVEL_COLORS[lvl]}33`,
        fontFamily: "monospace",
        fontSize: "0.7rem",
      }}
    />
  ));
  /** @type {React.ReactNode[]} */
  const headerCells = ["Timestamp", "Level", "Logger", "Message"].map((col) => (
    <Box
      key={col}
      component="th"
      sx={{
        px: 2,
        py: 1.5,
        textAlign: "left",
        fontWeight: 600,
        fontSize: "0.75rem",
        color: COMMON_COLORS.text.secondary,
        borderBottom: `1px solid ${themeColors.alpha.divider}`,
        textShadow: `0 0 15px ${themeColors.glow}20`,
      }}
    >
      {col}
    </Box>
  ));

  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <SectionCard
        title="Logs"
        icon={<ArticleIcon sx={{ color: "#fff", fontSize: 22 }} />}
        disableHover
        sx={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}
        contentSx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        }}
      >
        {/* ------------------------------------------------------------------ */}
        {/* Filter bar                                                           */}
        {/* ------------------------------------------------------------------ */}
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            gap: 2,
            mb: 2,
            alignItems: "center",
          }}
        >
          {/* File selector */}
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <Select
              variant="outlined"
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              displayEmpty
              sx={{ fontSize: "0.875rem" }}
            >
              <MenuItem value="">Current (app.log)</MenuItem>
              {fileOptions}
            </Select>
          </FormControl>

          {/* Level toggle chips */}
          <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>{levelFilterChips}</Box>

          {/* Search input */}
          <TextField
            size="small"
            placeholder="Search…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ fontSize: 18, color: COMMON_COLORS.text.muted }} />
                  </InputAdornment>
                ),
              },
            }}
            sx={{ flex: 1, minWidth: 160, maxWidth: 280 }}
          />

          {/* Auto-refresh toggle + manual refresh */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, ml: "auto" }}>
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
              }
              label={
                <Typography variant="caption" sx={{ color: COMMON_COLORS.text.muted }}>
                  Auto
                </Typography>
              }
              sx={{ m: 0 }}
            />
            <Tooltip title="Refresh">
              <span>
                <IconButton
                  size="small"
                  onClick={() => refetch()}
                  disabled={isFetching}
                  sx={{ color: themeColors.secondary.main }}
                >
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
        </Box>

        {/* ------------------------------------------------------------------ */}
        {/* Stats row                                                            */}
        {/* ------------------------------------------------------------------ */}
        <Box
          sx={{
            display: "flex",
            gap: 1,
            mb: 2,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          {levelSummaryChips}
          <Typography variant="caption" sx={{ color: COMMON_COLORS.text.muted, ml: 1 }}>
            {total} total
          </Typography>
        </Box>

        {/* Error banner */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to fetch logs: {errorMessage}
          </Alert>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* Log table                                                            */}
        {/* ------------------------------------------------------------------ */}
        <Box
          sx={{
            borderRadius: "12px",
            overflow: "auto",
            border: `1px solid ${themeColors.alpha.divider}`,
            mb: 2,
            flex: 1,
            minHeight: 0,
          }}
        >
          <Box component="table" sx={{ width: "100%", borderCollapse: "collapse" }}>
            {/* Table head — sticky so columns stay visible while scrolling */}
            <Box
              component="thead"
              sx={{
                background: themeColors.gradients.header,
                position: "sticky",
                top: 0,
                zIndex: 1,
              }}
            >
              <Box component="tr">{headerCells}</Box>
            </Box>

            {/* Table body */}
            <Box component="tbody">
              {isLoading ? (
                <Box component="tr">
                  <Box
                    component="td"
                    colSpan={4}
                    sx={{
                      px: 2,
                      py: 4,
                      textAlign: "center",
                      color: COMMON_COLORS.text.muted,
                      fontSize: "0.875rem",
                    }}
                  >
                    Loading…
                  </Box>
                </Box>
              ) : entries.length === 0 ? (
                <Box component="tr">
                  <Box
                    component="td"
                    colSpan={4}
                    sx={{
                      px: 2,
                      py: 4,
                      textAlign: "center",
                      color: COMMON_COLORS.text.muted,
                      fontSize: "0.875rem",
                    }}
                  >
                    No log entries found.
                  </Box>
                </Box>
              ) : (
                entries.map((entry, index) => (
                  <Box
                    component="tr"
                    key={index}
                    sx={{
                      borderBottom:
                        index !== entries.length - 1
                          ? `1px solid ${themeColors.alpha.card}`
                          : "none",
                      transition: "background 0.15s ease",
                      "&:hover": {
                        background: `${LEVEL_COLORS[entry.level]}0D`,
                        boxShadow: `inset 3px 0 10px ${themeColors.glow}15`,
                      },
                    }}
                  >
                    {/* Timestamp */}
                    <Box
                      component="td"
                      sx={{
                        px: 2,
                        py: 1.5,
                        fontFamily: "monospace",
                        fontSize: "0.7rem",
                        color: COMMON_COLORS.text.muted,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {entry.timestamp}
                    </Box>

                    {/* Level chip */}
                    <Box component="td" sx={{ px: 2, py: 1.5, whiteSpace: "nowrap" }}>
                      <Chip
                        label={entry.level}
                        size="small"
                        sx={{
                          backgroundColor: `${LEVEL_COLORS[entry.level]}33`,
                          color: LEVEL_COLORS[entry.level],
                          border: `1px solid ${LEVEL_COLORS[entry.level]}4D`,
                          fontWeight: 600,
                          fontSize: "0.65rem",
                          height: 20,
                        }}
                      />
                    </Box>

                    {/* Logger */}
                    <Box
                      component="td"
                      sx={{
                        px: 2,
                        py: 1.5,
                        fontFamily: "monospace",
                        fontSize: "0.7rem",
                        color: "#a78bfa",
                        maxWidth: 200,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {entry.logger}
                    </Box>

                    {/* Message */}
                    <Box
                      component="td"
                      sx={{
                        px: 2,
                        py: 1.5,
                        fontSize: "0.75rem",
                        color: COMMON_COLORS.text.tertiary,
                        whiteSpace: "pre-wrap",
                        wordBreak: "break-word",
                      }}
                    >
                      {entry.message}
                    </Box>
                  </Box>
                ))
              )}
            </Box>
          </Box>
        </Box>

        {/* ------------------------------------------------------------------ */}
        {/* Pagination                                                           */}
        {/* ------------------------------------------------------------------ */}
        {pageCount > 1 && (
          <Box sx={{ display: "flex", justifyContent: "center" }}>
            <Pagination
              count={pageCount}
              page={page}
              onChange={(_, v) => setPage(v)}
              color="primary"
              size="small"
            />
          </Box>
        )}
      </SectionCard>
    </Box>
  );
}
