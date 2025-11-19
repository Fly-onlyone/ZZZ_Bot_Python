import { useEffect, useState } from "react";
import { DEFAULT_PRIORITY_OFFSET } from "../config";

/**
 * useShoppingState Hook
 *
 * Manages shopping-related state including selected items and hunt mode items.
 * Handles initialization from API data and synchronization between selection and hunt items.
 *
 * @param {Object} shopping - Shopping data from API
 * @returns {Object} Shopping state and handlers
 *   - selectedRows: Array of selected items with priorities
 *   - huntItems: Array of item names in hunt mode
 *   - setSelectedRows: Update selected rows
 *   - setHuntItems: Update hunt items
 *   - handleHuntToggle: Toggle hunt mode for an item
 *   - handleRowSelectionChange: Handle DataGrid selection changes
 */
export function useShoppingState(shopping) {
  const [selectedRows, setSelectedRows] = useState([]);
  const [huntItems, setHuntItems] = useState([]);

  // Initialize state when shopping data is loaded
  useEffect(() => {
    if (shopping?.Selected) {
      setSelectedRows(
        shopping.Selected.map((name, index) => ({
          Name: name,
          Priority: index + DEFAULT_PRIORITY_OFFSET,
        }))
      );
    }
    if (shopping?.Hunt) {
      setHuntItems(shopping.Hunt);
    }
  }, [shopping]);

  /**
   * Toggle hunt mode for a specific item
   */
  const handleHuntToggle = (itemName) => {
    setHuntItems((prev) => {
      if (prev.includes(itemName)) {
        return prev.filter((name) => name !== itemName);
      } else {
        return [...prev, itemName];
      }
    });
  };

  /**
   * Handle row selection changes from DataGrid
   * Automatically removes hunt items that are no longer selected
   */
  const handleRowSelectionChange = (newSelection) => {
    const updatedRows = newSelection.map((name, index) => {
      const existing = selectedRows.find((row) => row.Name === name);
      return {
        Name: name,
        Priority: existing
          ? existing.Priority
          : index + DEFAULT_PRIORITY_OFFSET,
      };
    });

    setSelectedRows(updatedRows);

    // Auto-remove hunt items that are no longer selected for shopping
    setHuntItems((prevHuntItems) =>
      prevHuntItems.filter((huntItem) => newSelection.includes(huntItem))
    );
  };

  return {
    selectedRows,
    huntItems,
    setSelectedRows,
    setHuntItems,
    handleHuntToggle,
    handleRowSelectionChange,
  };
}
