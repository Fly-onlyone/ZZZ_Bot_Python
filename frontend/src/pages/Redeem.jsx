import { DataLoader } from "../services";
import { useLocation } from "react-router-dom";
import DoneIcon from "@mui/icons-material/Done";
import CloseIcon from "@mui/icons-material/Close";
import { DataGrid } from "@mui/x-data-grid";
import { Button } from "@mui/material";
import { useEffect, useState } from "react";
import RedeemIcon from "@mui/icons-material/Redeem";
import { EmptyState, SaveButton } from "../components";
import { logInfo, logWarn } from "../services/sentryLogger.js";

export default function Redeem() {
  const location = useLocation();
  const route = location.pathname.replace("/", "");

  const { useRouteData, useSaveData } = DataLoader();
  const { data: redeemList = [], error } = useRouteData(route);
  const { mutate: saveData } = useSaveData("redeem");

  const [rows, setRows] = useState([]);
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });

  useEffect(() => {
    const nextRows = redeemList.map((item, index) => ({
      id: index,
      ...item,
    }));

    setRows((prevRows) => {
      const previousSnapshot = JSON.stringify(prevRows);
      const nextSnapshot = JSON.stringify(nextRows);
      return previousSnapshot === nextSnapshot ? prevRows : nextRows;
    });
  }, [redeemList]);

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

  const handleSwitchState = (id) => {
    logInfo("Redeem item marked done", {
      itemId: id,
    });
    setRows((prevRows) =>
      prevRows.map((row) =>
        row.id === id ? { ...row, state: !row.state } : row
      )
    );
  };

  const handleSave = () => {
    saveData(rows, {
      onSuccess: () => {
        logInfo("Redeem save succeeded", {
          itemCount: rows.length,
        });
        setAlert({
          open: true,
          type: "success",
          message: "Redeem data updated successfully",
        });
      },
      onError: (saveError) => {
        logWarn("Redeem save failed in page handler", {
          error:
            saveError instanceof Error ? saveError.message : String(saveError),
          itemCount: rows.length,
        });
        setAlert({
          open: true,
          type: "error",
          message: "Failed to update redeem data",
        });
      },
    });
  };

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

  const columns = [
    { field: "id", headerName: "ID", flex: 0.5 },
    { field: "item_name", headerName: "Item Name", flex: 1 },
    { field: "code", headerName: "Code", flex: 1 },
    { field: "day", headerName: "Day", flex: 0.8 },
    {
      field: "state",
      headerName: "State",
      flex: 0.5,
      renderCell: (params) => (
        <div
          style={{ display: "flex", alignItems: "center", marginTop: "13px" }}
        >
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
            color="primary"
            onClick={() => handleSwitchState(params.row.id)}
          >
            DONE
          </Button>
        ) : null,
    },
  ];

  return (
    <div style={{ height: 420, minWidth: 320, width: "100%" }}>
      <DataGrid
        rows={rows}
        columns={columns}
        hideFooterSelectedRowCount
        sx={{ height: "100%", width: "100%" }}
      />
      <div className="flex justify-center">
        <SaveButton onSave={handleSave} alert={alert} setAlert={setAlert} />
      </div>
    </div>
  );
}
