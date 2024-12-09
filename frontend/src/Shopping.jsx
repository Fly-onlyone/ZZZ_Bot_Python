import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Alert, Box, Button, Grid2, Snackbar, Typography } from "@mui/material";
import { useLocation } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { DataLoader } from "./DataLoader";

export default function Shopping() {
  const [selectedRows, setSelectedRows] = useState([]); // Store selected row data (Name + Priority)
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });
  const location = useLocation();
  const route = location.pathname.replace("/", ""); // Extract route name dynamically
  const { useRouteData, useSaveData } = DataLoader();

  const { data: shopping, error } = useRouteData(route);
  const mutation = useSaveData(route);

  if (!shopping) {
    return <Typography>Loading...</Typography>; // Show a loading message
  }
  if (error) {
    return <Typography>Error loading data: {error.message}</Typography>; // Handle fetch error
  }

  // Initialize selected rows when data is available
  useEffect(() => {
    if (shopping?.Selected) {
      setSelectedRows(
        shopping.Selected.map((name, index) => ({
          Name: name,
          Priority: index + 1,
        }))
      );
    }
  }, [shopping]);
  // Convert shopping data into rows
  const rows = Object.entries(shopping["Item's list"]).map(([key, item]) => ({
    id: item.Name, // Use Name as the row ID
    ...item,
    Priority:
      selectedRows.find((row) => row.Name === item.Name)?.Priority || null, // Add priority if already selected
  }));

  // Define the columns
  const columns = [
    { field: "Name", headerName: "Name", flex: 2 },
    { field: "Price", headerName: "Price", flex: 1, type: "number" },
    { field: "Inventory", headerName: "Inventory", flex: 1, type: "number" },
    { field: "Available", headerName: "Available", flex: 1 },
    {
      field: "Priority",
      headerName: "Priority",
      flex: 1,
      type: "number",
      editable: true, // Allow manual editing of Priority
      renderCell: (params) => {
        const isSelected = selectedRows.some(
          (row) => row.Name === params.row.Name
        );
        return isSelected ? params.value : "N/A"; // Show "N/A" for unselected rows
      },
    },
  ];

  // Handle row selection
  const handleRowSelectionChange = (newSelection) => {
    const updatedRows = newSelection.map((name, index) => {
      const existing = selectedRows.find((row) => row.Name === name);
      return {
        Name: name,
        Priority: existing ? existing.Priority : index + 1, // Preserve Priority if already set
      };
    });

    setSelectedRows(updatedRows);
  };

  // Reorder priorities sequentially
  const reorderPriorities = () => {
    const reorderedRows = [...selectedRows]
      .sort((a, b) => a.Priority - b.Priority) // Sort by Priority
      .map((row, index) => ({ ...row, Priority: index + 1 })); // Reassign sequential priorities

    setSelectedRows(reorderedRows);
  };

  // Handle cell editing (stop event)
  const handleCellEditStop = (params, event) => {
    if (params.field === "Priority") {
      const newPriority = Number(event.target.value);

      if (!isNaN(newPriority)) {
        // Prevent editing if the item is not selected
        const editingRow = selectedRows.find((row) => row.Name === params.id);
        if (!editingRow) return;

        // Check for duplicates and handle swapping priorities
        const duplicateRow = selectedRows.find(
          (row) => row.Priority === newPriority && row.Name !== params.row.Name
        );

        const updatedRows = selectedRows.map((row) => {
          if (row.Name === params.id) {
            return { ...row, Priority: newPriority };
          } else if (duplicateRow && row.Name === duplicateRow.Name) {
            return { ...row, Priority: editingRow.Priority };
          }
          return row;
        });

        setSelectedRows(updatedRows);
        reorderPriorities();
      }
    }
  };

  const handleSave = () => {
    // Transform selectedRows to the required structure
    const payload = {
      Selected: selectedRows.map((row) => row.Name), // Extract only the Name field
    };

    console.log("Payload:", payload); // Log payload for debugging

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
          getRowId={(row) => row.Name} // Use Name as unique identifier
          rowSelectionModel={selectedRows.map((row) => row.Name)} // Pre-select rows by Name
          onRowSelectionModelChange={handleRowSelectionChange} // Update selected rows
          onCellEditStop={handleCellEditStop} // Handle Priority updates
        />
      </div>

      {/* Save Button */}
      <Button
        className="mt-2"
        variant="contained"
        color="primary"
        onClick={handleSave}
      >
        Save
      </Button>
      <Snackbar
        open={alert.open}
        autoHideDuration={3000}
        onClose={() => setAlert({ ...alert, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={alert.type} variant="outlined">
          {alert.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
