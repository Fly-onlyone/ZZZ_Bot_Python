import { DEFAULT_PRIORITY_OFFSET } from "../config";
import { logInfo, logWarn } from "../services/sentryLogger.js";

/**
 * usePriorityManagement Hook
 *
 * Handles priority editing and reordering logic for shopping items.
 * Implements priority swapping when duplicate priorities are assigned.
 *
 * @param {Array} selectedRows - Current selected rows with priorities
 * @param {Function} setSelectedRows - State setter for selected rows
 * @returns {Object} Priority management functions
 *   - processRowUpdate: Handle DataGrid row updates (priority changes)
 */
export function usePriorityManagement(selectedRows, setSelectedRows) {
  /**
   * Process row updates from DataGrid
   * Handles priority changes with automatic swapping and reordering
   *
   * @param {Object} newRow - Updated row data
   * @param {Object} oldRow - Original row data
   * @returns {Object} Final row data after processing
   */
  const processRowUpdate = (newRow, oldRow) => {
    const newPriority = Number(newRow.Priority);

    logInfo("Shopping priority edit requested", {
      itemName: oldRow.Name,
      newPriority,
    });

    // Validate priority value
    if (!isNaN(newPriority) && newPriority > 0) {
      const editingRowIndex = selectedRows.findIndex(
        (row) => row.Name === oldRow.Name
      );

      const duplicateRowIndex = selectedRows.findIndex(
        (row) => row.Priority === newPriority && row.Name !== oldRow.Name
      );

      const updatedRows = [...selectedRows];

      // If priority already exists, swap with that row
      if (duplicateRowIndex !== -1) {
        logInfo("Shopping priority swap applied", {
          itemName: updatedRows[editingRowIndex].Name,
          swappedWith: updatedRows[duplicateRowIndex].Name,
          requestedPriority: newPriority,
        });
        updatedRows[duplicateRowIndex].Priority =
          updatedRows[editingRowIndex].Priority;
      }

      // Update the editing row's priority
      updatedRows[editingRowIndex].Priority = newPriority;

      // Reorder all priorities to be sequential
      const reorderedRows = updatedRows
        .sort((a, b) => a.Priority - b.Priority)
        .map((row, index) => ({
          ...row,
          Priority: index + DEFAULT_PRIORITY_OFFSET,
        }));
      logInfo("Shopping priorities reordered", {
        selectedCount: reorderedRows.length,
      });

      // Save reordered rows to state
      setSelectedRows(reorderedRows);

      // Return the updated row for DataGrid
      return reorderedRows.find((row) => row.Name === newRow.Name);
    }

    logWarn("Shopping priority edit ignored", {
      itemName: oldRow.Name,
      newPriority: String(newRow.Priority),
    });
    return oldRow; // Fallback for invalid priority
  };

  return {
    processRowUpdate,
  };
}
