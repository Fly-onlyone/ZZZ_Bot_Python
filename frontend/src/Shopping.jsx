import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Chip, Grid2, Typography } from "@mui/material";
import { useLocation } from "react-router-dom";
import { DataLoader } from "./DataLoader";
import SaveButton from "./SaveButton";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ShoppingBagIcon from "@mui/icons-material/ShoppingBag";

export default function Shopping() {
  const [selectedRows, setSelectedRows] = useState([]); // Store selected row data (Name + Priority)
  const [huntItems, setHuntItems] = useState([]); // Store hunt item names
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

  // Initialize selected rows and hunt items when data is available
  useEffect(() => {
    if (shopping?.Selected) {
      setSelectedRows(
        shopping.Selected.map((name, index) => ({
          Name: name,
          Priority: index + 1,
        }))
      );
    }
    if (shopping?.Hunt) {
      setHuntItems(shopping.Hunt);
    }
  }, [shopping]);

  if (!shopping) {
    return <Typography>Loading...</Typography>; // Show a loading message
  }
  if (error) {
    return <Typography>Error loading data: {error.message}</Typography>; // Handle fetch error
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
      isPurchased: true, // Flag to identify purchased items
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

  // Handle hunt checkbox toggle
  const handleHuntToggle = (itemName) => {
    setHuntItems((prev) => {
      if (prev.includes(itemName)) {
        return prev.filter((name) => name !== itemName);
      } else {
        return [...prev, itemName];
      }
    });
  };

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
      editable: true, // Allow manual editing of Priority
      renderCell: (params) => {
        const isSelected = selectedRows.some(
          (row) => row.Name === params.row.Name
        );
        return isSelected ? params.value : "N/A"; // Show "N/A" for unselected rows
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
            className={`w-4 h-4 ${
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

    // Auto-remove hunt items that are no longer selected for shopping
    setHuntItems((prevHuntItems) =>
      prevHuntItems.filter((huntItem) => newSelection.includes(huntItem))
    );
  };

  const processRowUpdate = (newRow, oldRow) => {
    const newPriority = Number(newRow.Priority);

    console.log("Editing row:", oldRow.Name);
    console.log("New priority:", newPriority);

    if (!isNaN(newPriority) && newPriority > 0) {
      const editingRowIndex = selectedRows.findIndex(
        (row) => row.Name === oldRow.Name
      );

      const duplicateRowIndex = selectedRows.findIndex(
        (row) => row.Priority === newPriority && row.Name !== oldRow.Name
      );

      console.log("Duplicate row index:", duplicateRowIndex);

      const updatedRows = [...selectedRows];

      if (duplicateRowIndex !== -1) {
        // Swap priorities with the duplicate row
        console.log(
          `Swapping ${updatedRows[editingRowIndex].Name} with ${updatedRows[duplicateRowIndex].Name}`
        );
        updatedRows[duplicateRowIndex].Priority =
          updatedRows[editingRowIndex].Priority;
      }

      // Update the editing row's priority
      updatedRows[editingRowIndex].Priority = newPriority;

      // Reorder priorities
      const reorderedRows = updatedRows
        .sort((a, b) => a.Priority - b.Priority)
        .map((row, index) => ({ ...row, Priority: index + 1 }));

      console.log("Reordered rows:", reorderedRows);

      // Save reordered rows to state
      setSelectedRows(reorderedRows);

      // Return the updated row for DataGrid
      return reorderedRows.find((row) => row.Name === newRow.Name);
    }

    return oldRow; // Fallback in case of invalid priority
  };

  const handleSave = () => {
    // Transform selectedRows and huntItems to the required structure
    const payload = {
      Selected: selectedRows.map((row) => row.Name), // Extract only the Name field
      Hunt: huntItems, // Include hunt items
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
          getRowId={(row) => row.Name}
          rowSelectionModel={selectedRows.map((row) => row.Name)}
          onRowSelectionModelChange={handleRowSelectionChange}
          processRowUpdate={processRowUpdate}
          isCellEditable={(params) => {
            // Allow editing only for selected rows
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
