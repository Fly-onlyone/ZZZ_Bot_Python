import { createContext, useContext, useMemo } from "react";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Box, Checkbox, Tooltip, Typography } from "@mui/material";
import DragIndicatorIcon from "@mui/icons-material/DragIndicator";
import { useThemeContext } from "../../theme/ThemeContext";
import { COMMON_COLORS } from "../../theme/colors";
import { GLOW } from "../../theme/styles";

const GRID_TEMPLATE = "48px 56px minmax(200px, 1fr) 100px 100px 200px 100px 90px";
const ROW_BASE_TRANSITION = "background 0.2s ease-in-out, box-shadow 0.2s ease-in-out";

// Computed once at the table root and passed down through context so per-row
// renders don't rebuild the same sx tree on every theme-unrelated update.
const TableStylesContext = createContext(null);

function useTableStylesContext() {
  const ctx = useContext(TableStylesContext);
  if (!ctx) throw new Error("TableStylesContext is missing — wrap rows in <ShoppingItemsTable />");
  return ctx;
}

function buildTableStyles(themeColors) {
  return {
    themeColors,
    container: {
      border: `1px solid ${themeColors.alpha.cardBorder}`,
      borderRadius: "16px",
      background: themeColors.alpha.card,
      backdropFilter: "blur(8px)",
      overflow: "hidden",
      maxHeight: "calc(100vh - 240px)",
      overflowY: "auto",
    },
    headerRow: {
      display: "grid",
      gridTemplateColumns: GRID_TEMPLATE,
      background: themeColors.alpha.card,
      borderBottom: `1px solid ${themeColors.alpha.divider}`,
      position: "sticky",
      top: 0,
      zIndex: 2,
      backdropFilter: "blur(8px)",
    },
    headerCell: {
      px: 3,
      py: 2,
      fontFamily: '"Outfit", sans-serif',
      fontSize: "0.95rem",
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.05em",
      color: themeColors.primary.light,
      textShadow: `0 0 15px ${themeColors.glow}30`,
      display: "flex",
      alignItems: "center",
    },
    cell: {
      px: 3,
      py: 1.75,
      fontSize: "0.9375rem",
      display: "flex",
      alignItems: "center",
      borderBottom: `1px solid ${themeColors.alpha.divider}`,
    },
  };
}

function HeaderRow({ allSelected, someSelected, onSelectAllToggle }) {
  const { themeColors, headerRow, headerCell } = useTableStylesContext();
  return (
    <Box sx={headerRow}>
      <Box sx={{ ...headerCell, justifyContent: "center" }} aria-label="Move" />
      <Box sx={{ ...headerCell, justifyContent: "center" }}>
        <Checkbox
          size="small"
          checked={allSelected}
          indeterminate={someSelected}
          onChange={onSelectAllToggle}
          inputProps={{ "aria-label": "Select all items" }}
          sx={{
            p: 0.5,
            color: themeColors.alpha.divider,
            "&.Mui-checked, &.MuiCheckbox-indeterminate": {
              color: themeColors.primary.main,
            },
          }}
        />
      </Box>
      <Box sx={headerCell}>Name</Box>
      <Box sx={{ ...headerCell, justifyContent: "flex-end" }}>Price</Box>
      <Box sx={{ ...headerCell, justifyContent: "flex-end" }}>Stock</Box>
      <Box sx={headerCell}>Status</Box>
      <Box sx={{ ...headerCell, justifyContent: "center" }}>Priority</Box>
      <Box sx={{ ...headerCell, justifyContent: "center" }}>Hunt</Box>
    </Box>
  );
}

function ShoppingRow({
  row,
  priority,
  isSelected,
  isHunt,
  showDragHandle,
  dragHandleNodeRef,
  dragHandleListeners,
  dragHandleAttributes,
  rowRef,
  transform,
  transition,
  isDragging,
  onSelectionToggle,
  onHuntToggle,
}) {
  const { themeColors, cell } = useTableStylesContext();
  const isPurchased = row.isPurchased;
  const isHuntActive = isSelected && !isPurchased;

  const baseBg = isDragging
    ? themeColors.gradients.backgroundSubtle
    : isPurchased
      ? `${COMMON_COLORS.success.main}14`
      : isHunt
        ? `${COMMON_COLORS.warning.main}12`
        : "transparent";
  const hoverBg = isPurchased
    ? `${COMMON_COLORS.success.main}24`
    : isHunt
      ? `${COMMON_COLORS.warning.main}22`
      : themeColors.alpha.hover;
  const cellColor = isPurchased ? COMMON_COLORS.success.main : COMMON_COLORS.text.tertiary;
  const cellWeight = isPurchased || isHunt ? 500 : 400;

  const cellSx = {
    ...cell,
    color: cellColor,
    fontWeight: cellWeight,
  };

  return (
    <Box
      ref={rowRef}
      sx={{
        display: "grid",
        gridTemplateColumns: GRID_TEMPLATE,
        background: baseBg,
        transform,
        transition: isDragging
          ? (transition ?? ROW_BASE_TRANSITION)
          : transition
            ? `${transition}, ${ROW_BASE_TRANSITION}`
            : ROW_BASE_TRANSITION,
        opacity: isDragging ? 0.85 : 1,
        zIndex: isDragging ? 10 : "auto",
        position: "relative",
        boxShadow: isDragging ? GLOW.strong(themeColors.glow) : "none",
        "&:hover": { background: hoverBg, boxShadow: `inset 3px 0 10px ${themeColors.glow}15` },
      }}
    >
      {/* Drag handle column */}
      <Box sx={{ ...cellSx, justifyContent: "center", color: COMMON_COLORS.text.muted }}>
        {showDragHandle ? (
          <Box
            ref={dragHandleNodeRef}
            {...dragHandleAttributes}
            {...dragHandleListeners}
            role="button"
            tabIndex={0}
            aria-label={`Drag to reorder ${row.Name}`}
            sx={{
              cursor: "grab",
              "&:active": { cursor: "grabbing" },
              "&:hover": { color: themeColors.primary.light },
              "&:focus-visible": {
                outline: `2px solid ${themeColors.primary.main}`,
                outlineOffset: "2px",
              },
              display: "flex",
              alignItems: "center",
              p: 0.5,
              borderRadius: "6px",
              touchAction: "none",
            }}
          >
            <DragIndicatorIcon fontSize="small" />
          </Box>
        ) : null}
      </Box>

      {/* Select checkbox */}
      <Box sx={{ ...cellSx, justifyContent: "center" }}>
        <Checkbox
          size="small"
          checked={isSelected}
          onChange={() => onSelectionToggle(row.Name)}
          inputProps={{ "aria-label": `Select ${row.Name}` }}
          sx={{
            p: 0.5,
            color: themeColors.alpha.divider,
            "&.Mui-checked": { color: themeColors.primary.main },
          }}
        />
      </Box>

      {/* Name */}
      <Box sx={cellSx}>{row.Name}</Box>

      {/* Price */}
      <Box sx={{ ...cellSx, justifyContent: "flex-end" }}>{row.Price}</Box>

      {/* Stock */}
      <Box sx={{ ...cellSx, justifyContent: "flex-end" }}>{row.Inventory}</Box>

      {/* Status */}
      <Box sx={cellSx}>{row.Available}</Box>

      {/* Priority */}
      <Box
        sx={{
          ...cellSx,
          justifyContent: "center",
          color: priority != null ? themeColors.primary.light : COMMON_COLORS.text.muted,
          fontWeight: priority != null ? 600 : 400,
        }}
      >
        {priority != null ? `#${priority}` : "—"}
      </Box>

      {/* Hunt */}
      <Box sx={{ ...cellSx, justifyContent: "center" }}>
        {isHuntActive ? (
          <Checkbox
            size="small"
            checked={isHunt}
            onChange={() => onHuntToggle(row.Name)}
            inputProps={{ "aria-label": `Toggle hunt mode for ${row.Name}` }}
            sx={{
              p: 0.5,
              color: themeColors.alpha.divider,
              "&.Mui-checked": { color: COMMON_COLORS.warning.main },
            }}
          />
        ) : (
          <Tooltip title="Select a non-purchased item to enable hunt mode" arrow>
            <span>
              <Checkbox
                size="small"
                checked={false}
                disabled
                sx={{ p: 0.5, color: themeColors.alpha.divider }}
              />
            </span>
          </Tooltip>
        )}
      </Box>
    </Box>
  );
}

function SortableShoppingRow(props) {
  const sortable = useSortable({
    id: props.row.Name,
    disabled: props.row.isPurchased,
  });

  return (
    <ShoppingRow
      {...props}
      rowRef={sortable.setNodeRef}
      dragHandleNodeRef={sortable.setActivatorNodeRef}
      dragHandleListeners={sortable.listeners}
      dragHandleAttributes={sortable.attributes}
      transform={CSS.Transform.toString(sortable.transform)}
      transition={sortable.transition}
      isDragging={sortable.isDragging}
    />
  );
}

function SectionDivider({ label }) {
  const { themeColors } = useTableStylesContext();
  return (
    <Box
      sx={{
        px: 3,
        py: 1,
        background: `${themeColors.primary.main}0A`,
        borderBottom: `1px solid ${themeColors.alpha.divider}`,
        borderTop: `1px solid ${themeColors.alpha.divider}`,
      }}
    >
      <Typography
        variant="caption"
        sx={{
          color: themeColors.primary.light,
          fontWeight: 700,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          fontSize: "0.7rem",
          textShadow: `0 0 12px ${themeColors.glow}25`,
        }}
      >
        {label}
      </Typography>
    </Box>
  );
}

export default function ShoppingItemsTable({
  selectedRows,
  unselectedRows,
  huntItemsSet,
  selectedNamesSet,
  onSelectionToggle,
  onHuntToggle,
  onDragEnd,
  allSelected,
  someSelected,
  onSelectAllToggle,
}) {
  const { themeColors } = useThemeContext();
  const styles = useMemo(() => buildTableStyles(themeColors), [themeColors]);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  // Memoized so dnd-kit doesn't re-register the same sortable nodes on
  // theme-unrelated re-renders of the parent.
  const sortableIds = useMemo(
    () => selectedRows.filter((r) => !r.isPurchased).map((r) => r.Name),
    [selectedRows],
  );

  return (
    <TableStylesContext.Provider value={styles}>
      <Box sx={styles.container}>
        <HeaderRow
          allSelected={allSelected}
          someSelected={someSelected}
          onSelectAllToggle={onSelectAllToggle}
        />

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext items={sortableIds} strategy={verticalListSortingStrategy}>
            {selectedRows.map((row, index) => (
              <SortableShoppingRow
                key={row.Name}
                row={row}
                priority={index + 1}
                isSelected
                isHunt={huntItemsSet.has(row.Name)}
                showDragHandle={!row.isPurchased}
                onSelectionToggle={onSelectionToggle}
                onHuntToggle={onHuntToggle}
              />
            ))}
          </SortableContext>

          {selectedRows.length > 0 && unselectedRows.length > 0 && (
            <SectionDivider label={`Catalog · ${unselectedRows.length} items`} />
          )}

          {unselectedRows.map((row) => (
            <ShoppingRow
              key={row.Name}
              row={row}
              priority={null}
              isSelected={selectedNamesSet.has(row.Name)}
              isHunt={huntItemsSet.has(row.Name)}
              showDragHandle={false}
              onSelectionToggle={onSelectionToggle}
              onHuntToggle={onHuntToggle}
            />
          ))}
        </DndContext>
      </Box>
    </TableStylesContext.Provider>
  );
}
