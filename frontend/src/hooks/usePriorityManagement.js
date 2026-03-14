/**
 * usePriorityManagement Hook
 *
 * Previously handled priority editing and reordering in the DataGrid.
 * Priority management is now handled via drag-and-drop in SortableSelectedItems.
 * This hook is retained for backward compatibility.
 *
 * @param {Array} selectedRows - Current selected rows with priorities
 * @param {Function} setSelectedRows - State setter for selected rows
 * @returns {Object} Priority management functions
 */
export function usePriorityManagement(selectedRows, setSelectedRows) {
  return {};
}
