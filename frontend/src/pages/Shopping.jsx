import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Box, Grid2, Tab, Tabs, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useQueryClient } from "@tanstack/react-query";
import ShoppingCartIcon from "@mui/icons-material/ShoppingCart";
import { DataLoader } from "../services";
import { EmptyState, SaveStatus, ShoppingItemsTable, ShoppingSkeleton } from "../components";
import { useAutoSave, useShoppingState } from "../hooks";
import { logInfo, logWarn } from "../services/sentryLogger.js";
import { useThemeContext } from "../theme/ThemeContext";
import { getAuroraTabsStyles, auroraPanelVariants } from "../theme/tabStyles";

const LazyRedeem = React.lazy(() => import("./Redeem.jsx"));
const LazyHunt = React.lazy(() => import("../content/Hunt.jsx"));
const PENDING_HUNT_SCHEDULE = "Pending sync";

function applyShoppingSelection(shopping, payload) {
  return {
    ...(shopping || {}),
    Selected: payload.Selected,
    Hunt: payload.Hunt,
  };
}

function buildOptimisticHuntInfo(shopping, previousHuntInfo, payload, settings) {
  const settingsAvailable = settings && typeof settings === "object";
  const enabled = settingsAvailable
    ? settings.run_task !== false && settings.enable_hunt_mode === true
    : (previousHuntInfo?.enabled ?? false);
  const existingItems = new Map(
    (previousHuntInfo?.hunt_items || []).map((item) => [item.name, item]),
  );
  const itemList = shopping?.["Item's list"] || {};
  const huntItems = payload.Hunt.map((itemName) => {
    const existingItem = existingItems.get(itemName);
    const shoppingItem = itemList[itemName] || {};

    return {
      name: itemName,
      scheduled_time: existingItem?.scheduled_time || PENDING_HUNT_SCHEDULE,
      price: existingItem?.price ?? shoppingItem.Price ?? 0,
      inventory: existingItem?.inventory ?? shoppingItem.Inventory ?? 0,
    };
  });

  return {
    ...(previousHuntInfo || {}),
    enabled,
    hunt_items: huntItems,
    next_hunt_time:
      enabled && huntItems.length > 0 ? previousHuntInfo?.next_hunt_time || null : null,
  };
}

function TabFallback() {
  return <ShoppingSkeleton />;
}

function ShoppingItems() {
  const { useRouteData } = DataLoader();
  const queryClient = useQueryClient();
  const { data: shopping, error } = useRouteData("shopping");
  const { data: settings } = useRouteData("settings");
  const autoSave = useAutoSave("shopping");

  const commit = autoSave.commit;
  const handleShoppingChange = useCallback(
    (payload) => {
      const cachedShopping = queryClient.getQueryData(["shopping"]) || shopping;
      const cachedSettings = queryClient.getQueryData(["settings"]) || settings;
      const nextShopping = applyShoppingSelection(cachedShopping, payload);

      queryClient.setQueryData(["shopping"], nextShopping);
      queryClient.setQueryData(["overview/hunt"], (previousHuntInfo) =>
        buildOptimisticHuntInfo(nextShopping, previousHuntInfo, payload, cachedSettings),
      );

      logInfo("Shopping auto-save scheduled", {
        selectedCount: payload.Selected.length,
        huntCount: payload.Hunt.length,
      });
      commit(payload);
    },
    [commit, queryClient, settings, shopping],
  );

  const { selectedRows, huntItems, handleHuntToggle, handleRowSelectionChange, handleDragEnd } =
    useShoppingState(shopping, handleShoppingChange, autoSave.isPending);

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

  const itemList = useMemo(() => shopping?.["Item's list"] ?? {}, [shopping]);
  const purchasedItems = useMemo(() => shopping?.["Purchased"] ?? [], [shopping]);
  const hasItems = Object.keys(itemList).length > 0;
  const durationStart = shopping?.["Duration"]?.Start ?? "—";
  const durationEnd = shopping?.["Duration"]?.End ?? "—";

  // Build the unified row catalog. Each row is shaped for the table.
  const allRowsByName = useMemo(() => {
    if (!shopping) return new Map();
    const map = new Map();
    purchasedItems.forEach((itemName) => {
      map.set(itemName, {
        Name: itemName,
        Price: itemList[itemName]?.Price ?? "N/A",
        Inventory: itemList[itemName]?.Inventory ?? "N/A",
        Available: "Purchased",
        isPurchased: true,
      });
    });
    Object.entries(itemList).forEach(([, item]) => {
      if (!map.has(item.Name)) {
        map.set(item.Name, {
          Name: item.Name,
          Price: item.Price,
          Inventory: item.Inventory,
          Available: item.Available,
          isPurchased: false,
        });
      }
    });
    return map;
  }, [itemList, purchasedItems, shopping]);

  const huntItemsSet = useMemo(() => new Set(huntItems), [huntItems]);
  const selectedNamesSet = useMemo(
    () => new Set(selectedRows.map((row) => row.Name)),
    [selectedRows],
  );

  // Selected rows in priority order; unselected rows below.
  const selectedSection = useMemo(
    () => selectedRows.map((entry) => allRowsByName.get(entry.Name)).filter(Boolean),
    [selectedRows, allRowsByName],
  );
  const unselectedSection = useMemo(
    () => Array.from(allRowsByName.values()).filter((row) => !selectedNamesSet.has(row.Name)),
    [allRowsByName, selectedNamesSet],
  );

  const allNames = useMemo(() => Array.from(allRowsByName.keys()), [allRowsByName]);
  const allSelected = allNames.length > 0 && selectedRows.length === allNames.length;
  const someSelected = selectedRows.length > 0 && selectedRows.length < allNames.length;

  // Select-all toggles the entire catalog. Standard tri-state semantics:
  // checked → clear; indeterminate or empty → select all. When selecting all
  // from scratch, purchased items lead so the priority order keeps the
  // pinned-at-top convention.
  const handleSelectAllToggle = useCallback(() => {
    if (allSelected) {
      handleRowSelectionChange([]);
    } else {
      const purchasedFirst = [
        ...purchasedItems,
        ...allNames.filter((n) => !purchasedItems.includes(n)),
      ];
      handleRowSelectionChange(purchasedFirst);
    }
  }, [allSelected, purchasedItems, allNames, handleRowSelectionChange]);

  // Adapt checkbox-row toggle to the hook's selection handler. Purchased items
  // get re-inserted after the last purchased item already in the selected list
  // (keeps the purchased group pinned to the top of the priority order). Newly
  // selected non-purchased items append at the end.
  const handleSelectionToggle = useCallback(
    (name) => {
      const currentNames = selectedRows.map((row) => row.Name);
      let nextNames;
      if (currentNames.includes(name)) {
        nextNames = currentNames.filter((n) => n !== name);
      } else if (purchasedItems.includes(name)) {
        const lastPurchasedIdx = currentNames.findLastIndex((n) => purchasedItems.includes(n));
        nextNames = [
          ...currentNames.slice(0, lastPurchasedIdx + 1),
          name,
          ...currentNames.slice(lastPurchasedIdx + 1),
        ];
      } else {
        nextNames = [...currentNames, name];
      }
      handleRowSelectionChange(nextNames);
    },
    [selectedRows, purchasedItems, handleRowSelectionChange],
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

  return (
    <Box sx={{ p: 4 }}>
      <Grid2 container justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Point: {shopping.Point}</Typography>
        <SaveStatus status={autoSave.status} error={autoSave.error} onRetry={autoSave.retry} />
        <Typography variant="h6">
          Duration: {durationStart} - {durationEnd}
        </Typography>
      </Grid2>

      <ShoppingItemsTable
        selectedRows={selectedSection}
        unselectedRows={unselectedSection}
        huntItemsSet={huntItemsSet}
        selectedNamesSet={selectedNamesSet}
        onSelectionToggle={handleSelectionToggle}
        onHuntToggle={handleHuntToggle}
        onDragEnd={handleDragEnd}
        allSelected={allSelected}
        someSelected={someSelected}
        onSelectAllToggle={handleSelectAllToggle}
      />
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
