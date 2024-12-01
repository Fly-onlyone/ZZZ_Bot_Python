import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Alert, Box, Button, Grid2, Snackbar, Typography } from "@mui/material";

export default function Shopping() {
  const [shopping, setShopping] = useState(null); // Shopping data from backend
  const [selectedRows, setSelectedRows] = useState([]); // Store selected row data (Name + Priority)
  const BACKEND_URL = "http://127.0.0.1:8000";
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/shopping`);
        if (response.ok) {
          const data = await response.json();
          setShopping(data);

          // Load selected rows with priorities if present
          if (data.Selected) {
            setSelectedRows(
              data.Selected.map((name, index) => ({
                Name: name,
                Priority: index + 1, // Assign priority based on initial order
              }))
            );
          }
        } else {
          console.log(`Failed to fetch data: ${response.statusText}`);
        }
      } catch {
        console.log("An error occurred while fetching data.");
      }
    };
    fetchData();
  }, []);

  if (!shopping) {
    return <Typography>Loading...</Typography>; // Show a loading message
  }

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

  // Save the selected items (with Priority) to the backend
  const handleSave = async () => {
    const sortedRows = [...selectedRows].sort(
      (a, b) => a.Priority - b.Priority
    );
    try {
      const response = await fetch(`${BACKEND_URL}/shopping`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ Selected: sortedRows.map((row) => row.Name) }),
      });
      if (response.ok) {
        setAlert({
          open: true,
          type: "success",
          message: `Data saved successfully!`,
        });
      } else {
        console.log(`Failed to save data: ${response.statusText}`);
      }
    } catch {
      console.log("An error occurred while saving data.");
    }
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
