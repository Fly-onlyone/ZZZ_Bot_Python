import { useEffect, useRef, useState } from "react";
import { arrayMove } from "@dnd-kit/sortable";
import { DEFAULT_PRIORITY_OFFSET } from "../config";

/**
 * useShoppingState Hook
 *
 * Manages shopping-related state including selected items and hunt mode items.
 * Handles initialization from API data and synchronization between selection and hunt items.
 *
 * @param {Object} shopping - Shopping data from API
 * @param {(payload: {Selected: string[], Hunt: string[]}) => void} [onChange] - Fired after
 *   every user-action handler with the new payload. Hydration from `shopping` data does
 *   NOT fire this callback — only real user edits do, which makes it safe to wire directly
 *   to an auto-save commit.
 * @param {boolean} [skipHydration=false] - When true, the effect that copies `shopping.Selected`
 *   / `shopping.Hunt` into local state is suppressed. Consumers should set this true while an
 *   auto-save is pending so a mid-debounce refetch can't overwrite the user's unsaved edit.
 * @returns {Object} Shopping state and handlers
 */
export function useShoppingState(shopping, onChange, skipHydration = false) {
  const [selectedRows, setSelectedRows] = useState([]);
  const [huntItems, setHuntItems] = useState([]);

  // Refs mirror committed state so cross-handler notify() calls always read the
  // freshest values — closure-captured selectedRows/huntItems become stale when
  // a different handler updates them between this handler's renders.
  const selectedRowsRef = useRef(selectedRows);
  const huntItemsRef = useRef(huntItems);
  selectedRowsRef.current = selectedRows;
  huntItemsRef.current = huntItems;

  // Initialize state when shopping data is loaded. Gated by skipHydration so a
  // server refetch arriving mid-debounce doesn't clobber the user's pending edit.
  useEffect(() => {
    if (skipHydration) return;
    if (shopping?.Selected) {
      setSelectedRows(
        shopping.Selected.map((name, index) => ({
          Name: name,
          Priority: index + DEFAULT_PRIORITY_OFFSET,
        })),
      );
    }
    if (shopping?.Hunt) {
      setHuntItems(shopping.Hunt);
    }
  }, [shopping, skipHydration]);

  const notify = (nextSelected, nextHunt) => {
    if (typeof onChange !== "function") return;
    onChange({
      Selected: nextSelected.map((row) => row.Name),
      Hunt: nextHunt,
    });
  };

  /**
   * Toggle hunt mode for a specific item.
   *
   * Uses the setState updater form so rapid clicks always observe the latest
   * state — a closure-based read would lose toggles when two clicks fire before
   * React commits the first render. `notify` inside the updater is safe because
   * `commit` downstream is debounced, so StrictMode's double-invocation
   * collapses into a single save. Pairs the toggle with the latest selected
   * list via `selectedRowsRef` so a recent selection change isn't reverted by
   * an optimistic-cache write computed from a stale Selected array.
   */
  const handleHuntToggle = (itemName) => {
    setHuntItems((prev) => {
      const next = prev.includes(itemName)
        ? prev.filter((name) => name !== itemName)
        : [...prev, itemName];
      notify(selectedRowsRef.current, next);
      return next;
    });
  };

  /**
   * Handle row selection changes.
   *
   * Computes the next state synchronously from refs (mirroring committed
   * state) so `notify` can fire in the same tick — capturing it via the
   * setState updater closures wouldn't work because React 18 defers updater
   * invocation to the next render, leaving the captured locals null when the
   * post-setState code runs. Side effect: hunt items whose row got deselected
   * are silently pruned.
   */
  const handleRowSelectionChange = (newSelection) => {
    const newSelectionSet = new Set(newSelection);
    const prevSelected = selectedRowsRef.current;
    const nextSelected = newSelection.map((name, index) => {
      const existing = prevSelected.find((row) => row.Name === name);
      return {
        Name: name,
        Priority: existing ? existing.Priority : index + DEFAULT_PRIORITY_OFFSET,
      };
    });
    const nextHunt = huntItemsRef.current.filter((huntItem) => newSelectionSet.has(huntItem));

    setSelectedRows(nextSelected);
    setHuntItems(nextHunt);
    notify(nextSelected, nextHunt);
  };

  /**
   * Handle drag end from dnd-kit sortable list
   * Reorders items and reassigns sequential priorities
   */
  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    setSelectedRows((prev) => {
      const oldIndex = prev.findIndex((row) => row.Name === active.id);
      const newIndex = prev.findIndex((row) => row.Name === over.id);
      if (oldIndex === -1 || newIndex === -1) return prev;

      const reordered = arrayMove(prev, oldIndex, newIndex).map((row, index) => ({
        ...row,
        Priority: index + DEFAULT_PRIORITY_OFFSET,
      }));
      notify(reordered, huntItemsRef.current);
      return reordered;
    });
  };

  /**
   * Handle inline priority edit from DataGrid
   * Moves item to the new priority position and reassigns sequential priorities
   */
  const handlePriorityEdit = (itemName, newPriority) => {
    setSelectedRows((prev) => {
      const currentIndex = prev.findIndex((row) => row.Name === itemName);
      if (currentIndex === -1) return prev;

      const clampedPriority = Math.max(1, Math.min(newPriority, prev.length));
      const targetIndex = clampedPriority - DEFAULT_PRIORITY_OFFSET;
      if (currentIndex === targetIndex) return prev;

      const reordered = arrayMove(prev, currentIndex, targetIndex).map((row, index) => ({
        ...row,
        Priority: index + DEFAULT_PRIORITY_OFFSET,
      }));
      notify(reordered, huntItemsRef.current);
      return reordered;
    });
  };

  return {
    selectedRows,
    huntItems,
    setSelectedRows,
    setHuntItems,
    handleHuntToggle,
    handleRowSelectionChange,
    handleDragEnd,
    handlePriorityEdit,
  };
}
