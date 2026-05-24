import React, { useEffect, useMemo, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Grid2, Tab, Tabs, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import TrackChangesIcon from "@mui/icons-material/TrackChanges";
import { DataLoader } from "../services";
import { EmptyState, SaveButton, ShoppingSkeleton, SortableSelectedItems } from "../components";
import { useShoppingState } from "../hooks";
import { logError, logInfo, logWarn } from "../services/sentryLogger.js";
import { useThemeContext } from "../theme/ThemeContext";
import { COMMON_COLORS } from "../theme/colors";
import { getAuroraTabsStyles, auroraPanelVariants } from "../theme/tabStyles";

const LazyRedeem = React.lazy(() => import("./Redeem.jsx"));
const LazyHunt = React.lazy(() => import("../content/Hunt.jsx"));

function TabFallback() {
  return <ShoppingSkeleton />;
}

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
    handlePriorityEdit,
  } = useShoppingState(shopping);

  useEffect(() => {
    if (!shopping) {
      return;
    }

    logInfo("Shopping page data ready", {
      itemCount: Object.keys(shopping["Item's list"] || {}).length,
      purchasedCount: (shopping["Purchased"] || []).length,
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

  const itemList = shopping?.["Item's list"] ?? {};
  const purchasedItems = shopping?.["Purchased"] ?? [];
  const hasItems = Object.keys(itemList).length > 0;
  const durationStart = shopping?.["Duration"]?.Start ?? "—";
  const durationEnd = shopping?.["Duration"]?.End ?? "—";

  // Keep hook order stable while data is loading or unavailable.
  const rows = useMemo(() => {
    if (!shopping) {
      return [];
    }

    const priorityMap = new Map(selectedRows.map((row) => [row.Name, row.Priority]));
    return [
      ...purchasedItems.map((itemName) => ({
        id: itemName,
        Name: itemName,
        Price: itemList[itemName]?.Price || "N/A",
        Inventory: itemList[itemName]?.Inventory || "N/A",
        Available: "Purchased",
        Priority: priorityMap.get(itemName) || null,
        isPurchased: true,
      })),
      ...Object.entries(itemList)
        .filter(([, item]) => !purchasedItems.includes(item.Name))
        .map(([, item]) => ({
          id: item.Name,
          ...item,
          Priority: priorityMap.get(item.Name) || null,
          isPurchased: false,
        })),
    ];
  }, [itemList, purchasedItems, selectedRows, shopping]);

  const huntItemsSet = useMemo(() => new Set(huntItems), [huntItems]);
  const selectedNamesSet = useMemo(
    () => new Set(selectedRows.map((row) => row.Name)),
    [selectedRows]
  );
  const rowSelectionModel = useMemo(() => selectedRows.map((row) => row.Name), [selectedRows]);
  const columns = useMemo(
    () => [
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
        flex: 0.8,
        type: "number",
        editable: true,
        renderCell: (params) => (selectedNamesSet.has(params.row.Name) ? params.value : "—"),
      },
      {
        field: "Hunt",
        headerName: "Hunt",
        flex: 0.6,
        sortable: false,
        filterable: false,
        renderCell: (params) => {
          if (!huntItemsSet.has(params.row.Name)) {
            return null;
          }

          return (
            <TrackChangesIcon
              sx={{
                color: COMMON_COLORS.warning.main,
                fontSize: 20,
                filter: `drop-shadow(0 0 4px ${COMMON_COLORS.warning.main}60)`,
              }}
            />
          );
        },
      },
    ],
    [huntItemsSet, selectedNamesSet]
  );

  const processRowUpdate = React.useCallback(
    (newRow, oldRow) => {
      try {
        if (newRow.Priority !== oldRow.Priority && newRow.Priority != null) {
          const isSelected = selectedNamesSet.has(newRow.Name);
          if (isSelected) {
            handlePriorityEdit(newRow.Name, newRow.Priority);
          }
        }
      } catch (e) {
        logError("Priority edit failed", e);
      }
      return newRow;
    },
    [handlePriorityEdit, selectedNamesSet]
  );

  const isCellEditable = React.useCallback(
    (params) => {
      if (params.field !== "Priority") return false;
      return selectedNamesSet.has(params.row.Name);
    },
    [selectedNamesSet]
  );
  const getRowClassName = React.useCallback(
    (params) => {
      const classes = [];
      if (params.row.isPurchased) classes.push("purchased-row");
      if (huntItemsSet.has(params.row.Name)) classes.push("hunt-row");
      return classes.join(" ");
    },
    [huntItemsSet]
  );

  if (!shopping) {
    return <ShoppingSkeleton />;
  }
  if (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return <Typography>Error loading data: {errorMessage}</Typography>;
  }

  if (!hasItems) {
    return (
      <EmptyState
        icon={<ShoppingCartIcon />}
        title="No Items Available"
        subtitle="The shop item list is empty. Run the bot to gather shopping data first."
      />
    );
  }

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
      <Grid2 container justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Point: {shopping.Point}</Typography>
        <Typography variant="h6">
          Duration: {durationStart} - {durationEnd}
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
          rowSelectionModel={rowSelectionModel}
          onRowSelectionModelChange={handleRowSelectionChange}
          processRowUpdate={processRowUpdate}
          onProcessRowUpdateError={(error) => logError("DataGrid row update failed", error)}
          isCellEditable={isCellEditable}
          getRowClassName={getRowClassName}
          rowBufferPx={60}
          columnBufferPx={60}
          sx={{
            "& .purchased-row": {
              background: `${COMMON_COLORS.success.main}14`,
              "&:hover": {
                background: `${COMMON_COLORS.success.main}20`,
              },
            },
            "& .purchased-row .MuiDataGrid-cell": {
              color: COMMON_COLORS.success.main,
              fontWeight: 500,
            },
            "& .hunt-row": {
              background: `${COMMON_COLORS.warning.main}12`,
              "&:hover": {
                background: `${COMMON_COLORS.warning.main}20`,
              },
            },
            "& .hunt-row .MuiDataGrid-cell": {
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
          <React.Suspense fallback={<TabFallback />}>
            {activeTab === 0 && <ShoppingItems />}
            {activeTab === 1 && <LazyRedeem />}
            {activeTab === 2 && <LazyHunt />}
          </React.Suspense>
        </Box>
      </AnimatePresence>
    </Box>
  );
}
