import React, { useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Grid2, Typography } from "@mui/material";
import { useLocation } from "react-router-dom";
import { DataLoader } from "../services";
import { SaveButton } from "../components";
import { usePriorityManagement, useShoppingState } from "../hooks";

export default function Shopping() {
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });

  const location = useLocation();
  const route = location.pathname.replace("/", "");
  const { useRouteData, useSaveData } = DataLoader();
  const { data: shopping, error } = useRouteData(route);
  const mutation = useSaveData(route);

  // Use custom hooks for state management
  const {
    selectedRows,
    huntItems,
    setSelectedRows,
    handleHuntToggle,
    handleRowSelectionChange,
  } = useShoppingState(shopping);

  const { processRowUpdate } = usePriorityManagement(
    selectedRows,
    setSelectedRows
  );

  if (!shopping) {
    return <Typography>Loading...</Typography>;
  }
  if (error) {
    return <Typography>Error loading data: {error.message}</Typography>;
  }

  // Convert shopping data into rows and add purchased items
  const rows = [
    // Add purchased items first
    ...(shopping.Purchased || []).map((itemName) => ({
      id: itemName,
      Name: itemName,
      Price: shopping["Item's list"][itemName]?.Price || "N/A",
      Inventory: shopping["Item's list"][itemName]?.Inventory || "N/A",
      Available: "Purchased",
      Priority:
        selectedRows.find((row) => row.Name === itemName)?.Priority || null,
      isPurchased: true,
    })),
    // Add regular shopping items
    ...Object.entries(shopping["Item's list"])
      .filter(([key, item]) => !(shopping.Purchased || []).includes(item.Name))
      .map(([key, item]) => ({
        id: item.Name,
        ...item,
        Priority:
          selectedRows.find((row) => row.Name === item.Name)?.Priority || null,
        isPurchased: false,
      })),
  ];

  // Define the columns
  const columns = [
    { field: "Name", headerName: "Name", flex: 2 },
    {
      field: "Price",
      headerName: "Price",
      flex: 1,
      type: "number",
    },
    { field: "Inventory", headerName: "Inventory", flex: 1, type: "number" },
    {
      field: "Available",
      headerName: "Available",
      flex: 1,
    },
    {
      field: "Priority",
      headerName: "Priority",
      flex: 1,
      type: "number",
      editable: true,
      renderCell: (params) => {
        const isSelected = selectedRows.some(
          (row) => row.Name === params.row.Name
        );
        return isSelected ? params.value : "N/A";
      },
    },
    {
      field: "Hunt",
      headerName: "Hunt",
      flex: 0.5,
      renderCell: (params) => {
        const isSelected = selectedRows.some(
          (row) => row.Name === params.row.Name
        );
        return (
          <input
            type="checkbox"
            checked={huntItems.includes(params.row.Name)}
            onChange={() => handleHuntToggle(params.row.Name)}
            disabled={!isSelected}
            className={`h-4 w-4 ${
              isSelected ? "cursor-pointer" : "cursor-not-allowed opacity-50"
            }`}
            title={
              isSelected
                ? "Enable hunt mode for this item"
                : "Select item for shopping first"
            }
          />
        );
      },
    },
  ];

  const handleSave = () => {
    const payload = {
      Selected: selectedRows.map((row) => row.Name),
      Hunt: huntItems,
    };

    console.log("Payload:", payload);

    mutation.mutate(payload, {
      onSuccess: () => {
        setAlert({
          open: true,
          type: "success",
          message: "Data saved successfully!",
        });
      },
      onError: (error) => {
        console.error("Save error:", error);
        setAlert({
          open: true,
          type: "error",
          message: "Error saving data.",
        });
      },
    });
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* Header Section */}
      <Grid2
        container
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 2 }}
      >
        <Typography variant="h6">Point: {shopping.Point}</Typography>
        <Typography variant="h6">
          Duration: {shopping.Duration.Start} - {shopping.Duration.End}
        </Typography>
      </Grid2>

      {/* Data Grid */}
      <div className="flex flex-col">
        <DataGrid
          rows={rows}
          columns={columns}
          checkboxSelection
          disableRowSelectionOnClick
          getRowId={(row) => row.Name}
          rowSelectionModel={selectedRows.map((row) => row.Name)}
          onRowSelectionModelChange={handleRowSelectionChange}
          processRowUpdate={processRowUpdate}
          isCellEditable={(params) => {
            return selectedRows.some((row) => row.Name === params.row.Name);
          }}
          getRowClassName={(params) =>
            params.row.isPurchased ? "purchased-row" : ""
          }
          sx={{
            "& .purchased-row": {
              background:
                "linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)",
              "&:hover": {
                background:
                  "linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%)",
              },
            },
            "& .purchased-row .MuiDataGrid-cell": {
              color: "#10b981",
              fontWeight: 500,
            },
          }}
        />
      </div>

      {/* Save Button */}
      <SaveButton onSave={handleSave} alert={alert} setAlert={setAlert} />
    </Box>
  );
}
