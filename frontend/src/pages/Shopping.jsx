import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Grid2, Tab, Tabs, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import { DataLoader } from "../services";
import {
  EmptyState,
  SaveButton,
  ShoppingSkeleton,
  SortableSelectedItems,
} from "../components";
import { useShoppingState } from "../hooks";
import { logInfo, logWarn } from "../services/sentryLogger.js";
import Redeem from "./Redeem";
import Hunt from "../content/Hunt";
import { useThemeContext } from "../theme/ThemeContext";
import { getAuroraTabsStyles, auroraPanelVariants } from "../theme/tabStyles";

function ShoppingItems() {
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });

  const { useRouteData, useSaveData } = DataLoader();
  const { data: shopping, error } = useRouteData("shopping");
  const mutation = useSaveData("shopping");

  const {
    selectedRows,
    huntItems,
    handleHuntToggle,
    handleRowSelectionChange,
    handleDragEnd,
  } = useShoppingState(shopping);

  useEffect(() => {
    if (!shopping) {
      return;
    }

    logInfo("Shopping page data ready", {
      itemCount: Object.keys(shopping["Item's list"] || {}).length,
      purchasedCount: (shopping.Purchased || []).length,
      selectedCount: selectedRows.length,
      point: shopping.Point ?? 0,
    });
  }, [selectedRows.length, shopping]);

  useEffect(() => {
    if (!error) {
      return;
    }

    logWarn("Shopping page data load failed", {
      error: error instanceof Error ? error.message : String(error),
    });
  }, [error]);

  if (!shopping) {
    return <ShoppingSkeleton />;
  }
  if (error) {
    return <Typography>Error loading data: {error.message}</Typography>;
  }

  if (
    !shopping["Item's list"] ||
    Object.keys(shopping["Item's list"]).length === 0
  ) {
    return (
      <EmptyState
        icon={<ShoppingCartIcon />}
        title="No Items Available"
        subtitle="The shop item list is empty. Run the bot to gather shopping data first."
      />
    );
  }

  // Convert shopping data into rows and add purchased items
  const rows = [
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
    ...Object.entries(shopping["Item's list"])
      .filter(([, item]) => !(shopping.Purchased || []).includes(item.Name))
      .map(([, item]) => ({
        id: item.Name,
        ...item,
        Priority:
          selectedRows.find((row) => row.Name === item.Name)?.Priority || null,
        isPurchased: false,
      })),
  ];

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
      renderCell: (params) => {
        const isSelected = selectedRows.some(
          (row) => row.Name === params.row.Name
        );
        return isSelected ? params.value : "N/A";
      },
    },
  ];

  const handleSave = () => {
    const payload = {
      Selected: selectedRows.map((row) => row.Name),
      Hunt: huntItems,
    };

    logInfo("Shopping save payload prepared", {
      selectedCount: payload.Selected.length,
      huntCount: payload.Hunt.length,
    });

    mutation.mutate(payload, {
      onSuccess: () => {
        logInfo("Shopping save succeeded", {
          selectedCount: payload.Selected.length,
          huntCount: payload.Hunt.length,
        });
        setAlert({
          open: true,
          type: "success",
          message: "Data saved successfully!",
        });
      },
      onError: (error) => {
        logWarn("Shopping save failed in page handler", {
          error: error instanceof Error ? error.message : String(error),
          selectedCount: payload.Selected.length,
          huntCount: payload.Hunt.length,
        });
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

      {/* Sortable Selected Items */}
      <SortableSelectedItems
        selectedRows={selectedRows}
        huntItems={huntItems}
        onDragEnd={handleDragEnd}
        onHuntToggle={handleHuntToggle}
      />

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

export default function Shopping() {
  const [activeTab, setActiveTab] = useState(0);
  const [tabDirection, setTabDirection] = useState(1);
  const { themeColors } = useThemeContext();

  const handleTabChange = (_, newValue) => {
    setTabDirection(newValue >= activeTab ? 1 : -1);
    setActiveTab(newValue);
  };

  return (
    <Box>
      <Tabs
        value={activeTab}
        onChange={handleTabChange}
        centered
        sx={getAuroraTabsStyles(themeColors)}
      >
        <Tab label="Items" />
        <Tab label="Redeem Codes" />
        <Tab label="Hunt Mode" />
      </Tabs>

      <AnimatePresence mode="wait" initial={false} custom={tabDirection}>
        <Box
          key={activeTab}
          component={motion.div}
          custom={tabDirection}
          variants={auroraPanelVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          {activeTab === 0 && <ShoppingItems />}
          {activeTab === 1 && <Redeem />}
          {activeTab === 2 && <Hunt />}
        </Box>
      </AnimatePresence>
    </Box>
  );
}
