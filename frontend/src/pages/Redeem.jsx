import { DataLoader } from "../services";
import DoneIcon from "@mui/icons-material/Done";
import CloseIcon from "@mui/icons-material/Close";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Button } from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import RedeemIcon from "@mui/icons-material/Redeem";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { EmptyState, RedeemSkeleton, SaveStatus } from "../components";
import { useAutoSave } from "../hooks";
import { logInfo, logWarn } from "../services/sentryLogger.js";

export default function Redeem() {
  const { useRouteData } = DataLoader();
  const { data: redeemList = [], isLoading, error } = useRouteData("redeem");
  const autoSave = useAutoSave("redeem");

  const [rows, setRows] = useState([]);

  // Gate hydration on autoSave.isPending so a server refetch landing inside
  // the debounce window can't overwrite the user's just-clicked DONE before
  // the save fires.
  const autoSaveIsPending = autoSave.isPending;
  useEffect(() => {
    if (autoSaveIsPending) return;
    const nextRows = redeemList.map((item, index) => ({
      id: index,
      ...item,
    }));

    setRows((prevRows) => {
      const previousSnapshot = JSON.stringify(prevRows);
      const nextSnapshot = JSON.stringify(nextRows);
      return previousSnapshot === nextSnapshot ? prevRows : nextRows;
    });
  }, [autoSaveIsPending, redeemList]);

  // Depend on length, not the array identity — TanStack Query returns a fresh
  // reference on every background refetch even when contents are unchanged.
  const redeemCount = redeemList.length;
  useEffect(() => {
    logInfo("Redeem page data ready", { itemCount: redeemCount });
  }, [redeemCount]);

  useEffect(() => {
    if (!error) {
      return;
    }

    logWarn("Redeem page data load failed", {
      error: error instanceof Error ? error.message : String(error),
    });
  }, [error]);

  // Auto-save fires directly from the user-action handler — never from a
  // state-watching effect. Server-driven row changes (hydration, refetch)
  // bypass this and so never trigger a save.
  //
  // Use the setRows updater form so the click handler — closed over by the
  // columns useMemo from the first render — always sees the freshest rows.
  // commit() inside the updater is safe because it's debounced; StrictMode's
  // double-invocation collapses into one save.
  const commit = autoSave.commit;
  const handleSwitchState = useCallback(
    (id) => {
      logInfo("Redeem item marked done", {
        itemId: id,
      });
      setRows((prev) => {
        const next = prev.map((row) => (row.id === id ? { ...row, state: !row.state } : row));
        commit(next);
        return next;
      });
    },
    [commit],
  );

  // Hooks must run before any conditional return to keep render order stable.
  const columns = useMemo(
    () => [
      { field: "id", headerName: "ID", flex: 0.5 },
      { field: "item_name", headerName: "Item Name", flex: 1 },
      { field: "code", headerName: "Code", flex: 1 },
      { field: "day", headerName: "Day", flex: 0.8 },
      {
        field: "state",
        headerName: "State",
        flex: 0.5,
        renderCell: (params) => (
          <Box sx={{ display: "flex", alignItems: "center", height: "100%" }}>
            {params.value ? <DoneIcon /> : <CloseIcon />}
          </Box>
        ),
      },
      {
        field: "action",
        headerName: "Action",
        flex: 0.8,
        renderCell: (params) =>
          params.row.state ? (
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                height: "100%",
                color: "text.disabled",
              }}
            >
              —
            </Box>
          ) : (
            <Button
              variant="contained"
              startIcon={<CheckCircleIcon />}
              onClick={() => handleSwitchState(params.row.id)}
              sx={{ fontWeight: 600 }}
            >
              DONE
            </Button>
          ),
      },
    ],
    [handleSwitchState],
  );

  if (isLoading && redeemList.length === 0) {
    return <RedeemSkeleton />;
  }

  if (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return <p className="text-red-500">{errorMessage}</p>;
  }

  if (redeemList.length === 0) {
    return (
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <EmptyState
          icon={<RedeemIcon />}
          title="No Redemption Codes"
          subtitle="No codes available yet. Codes will appear here after shopping exchanges."
        />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        flex: 1,
        minWidth: 320,
        minHeight: 0,
        width: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          flexShrink: 0,
          display: "flex",
          justifyContent: "flex-end",
          alignItems: "center",
          px: 1,
          py: 1,
          minHeight: 28,
          // Pin to single line — multi-line content would steal grid height.
          whiteSpace: "nowrap",
          overflow: "hidden",
        }}
      >
        <SaveStatus status={autoSave.status} error={autoSave.error} onRetry={autoSave.retry} />
      </Box>
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          width: "100%",
          position: "relative",
          // Theme applies 16px borderRadius to MuiDataGrid-root; clip inner
          // backgrounds (header backdrop, scrollbar) to the rounded corners.
          overflow: "hidden",
          borderRadius: "16px",
        }}
      >
        <DataGrid
          rows={rows}
          columns={columns}
          // Show pagination footer if rows exceed the MIT pageSize cap so older
          // codes stay reachable; otherwise hide it for the scroll-only layout.
          hideFooter={rows.length <= 100}
          rowBufferPx={60}
          columnBufferPx={60}
          initialState={{ pagination: { paginationModel: { pageSize: 100 } } }}
          sx={{
            position: "absolute",
            inset: 0,
          }}
        />
      </Box>
    </Box>
  );
}
