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

  useEffect(() => {
    logInfo("Redeem page data ready", {
      itemCount: redeemList.length,
    });
  }, [redeemList]);

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
          <div style={{ display: "flex", alignItems: "center", marginTop: "13px" }}>
            {params.value ? <DoneIcon /> : <CloseIcon />}
          </div>
        ),
      },
      {
        field: "action",
        headerName: "Action",
        flex: 0.8,
        renderCell: (params) =>
          !params.row.state ? (
            <Button
              variant="contained"
              startIcon={<CheckCircleIcon />}
              onClick={() => handleSwitchState(params.row.id)}
              sx={{ fontWeight: 600 }}
            >
              DONE
            </Button>
          ) : null,
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
      <EmptyState
        icon={<RedeemIcon />}
        title="No Redemption Codes"
        subtitle="No codes available yet. Codes will appear here after shopping exchanges."
      />
    );
  }

  return (
    <div style={{ minWidth: 320, width: "100%" }}>
      <Box sx={{ display: "flex", justifyContent: "flex-end", px: 1, py: 1, minHeight: 28 }}>
        <SaveStatus status={autoSave.status} error={autoSave.error} onRetry={autoSave.retry} />
      </Box>
      <div style={{ height: 420, width: "100%" }}>
        <DataGrid
          rows={rows}
          columns={columns}
          hideFooterSelectedRowCount
          rowBufferPx={60}
          columnBufferPx={60}
          sx={{ height: "100%", width: "100%" }}
        />
      </div>
    </div>
  );
}
