import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Typography, Grid2, Button } from "@mui/material";

export default function Shopping() {
  const [shopping, setShopping] = useState(null); // Shopping data from backend
  const [selectedRows, setSelectedRows] = useState([]); // Store selected row IDs
  const BACKEND_URL = "http://127.0.0.1:8000";

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/shopping`);
        if (response.ok) {
          const data = await response.json();
          setShopping(data);

          // Load selected rows if present
          if (data.Selected) {
            setSelectedRows(data.Selected);
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

  const rows = Object.entries(shopping["Item's list"]).map(([id, item]) => ({
    id, // Use the key as the row ID
    ...item,
  }));

  const columns = [
    { field: "Name", headerName: "Name", flex: 2 },
    { field: "Price", headerName: "Price", flex: 1, type: "number" },
    { field: "Inventory", headerName: "Inventory", flex: 1, type: "number" },
    { field: "Available", headerName: "Available", flex: 1 },
  ];

  const handleSave = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/shopping`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ Selected: selectedRows }),
      });
      if (response.ok) {
        console.log("Data saved successfully!");
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
      <div className="flex flex-col" style={{ height: 400 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          checkboxSelection
          rowSelectionModel={selectedRows} // Pre-select rows
          onRowSelectionModelChange={(newSelection) => {
            setSelectedRows(newSelection); // Update selected row IDs
          }}
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
    </Box>
  );
}
