import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
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
import { Box, Checkbox, Paper, Typography } from "@mui/material";
import DragIndicatorIcon from "@mui/icons-material/DragIndicator";
import { useThemeContext } from "../../theme/ThemeContext";
import { COMMON_COLORS } from "../../theme/colors";
import { GLOW } from "../../theme/styles";

function SortableItem({ item, index, huntItems, onHuntToggle }) {
  const { themeColors } = useThemeContext();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.Name,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 10 : "auto",
    opacity: isDragging ? 0.8 : 1,
  };

  return (
    <Paper
      ref={setNodeRef}
      style={style}
      elevation={isDragging ? 4 : 0}
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 2,
        px: 2,
        py: 1.5,
        mb: 0.5,
        borderRadius: "10px",
        background: isDragging ? themeColors.gradients.backgroundSubtle : "transparent",
        border: `1px solid ${
          isDragging ? themeColors.primary.main + "60" : themeColors.alpha.divider
        }`,
        boxShadow: isDragging ? GLOW.strong(themeColors.glow) : "none",
        cursor: "default",
        "&:hover": {
          background: themeColors.alpha.card,
        },
      }}
    >
      <Box
        {...attributes}
        {...listeners}
        sx={{
          display: "flex",
          alignItems: "center",
          cursor: "grab",
          color: COMMON_COLORS.text.muted,
          "&:hover": { color: themeColors.primary.light },
          "&:active": { cursor: "grabbing" },
        }}
      >
        <DragIndicatorIcon fontSize="small" />
      </Box>

      <Typography
        sx={{
          color: themeColors.primary.light,
          fontWeight: 700,
          fontSize: "0.75rem",
          minWidth: 24,
          textAlign: "center",
          background: `${themeColors.primary.main}1A`,
          borderRadius: "6px",
          px: 1,
          py: 0.25,
        }}
      >
        {index + 1}
      </Typography>

      <Typography
        sx={{
          flex: 1,
          color: COMMON_COLORS.text.tertiary,
          fontWeight: 500,
          fontSize: "0.875rem",
        }}
      >
        {item.Name}
      </Typography>

      <Checkbox
        size="small"
        checked={huntItems.includes(item.Name)}
        onChange={() => onHuntToggle(item.Name)}
        title="Enable hunt mode for this item"
        sx={{
          color: COMMON_COLORS.text.muted,
          "&.Mui-checked": {
            color: themeColors.primary.main,
          },
        }}
      />
    </Paper>
  );
}

export default function SortableSelectedItems({
  selectedRows,
  huntItems,
  onDragEnd,
  onHuntToggle,
}) {
  const { themeColors } = useThemeContext();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  if (selectedRows.length === 0) return null;

  return (
    <Box sx={{ mb: 3 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 1,
          px: 1,
        }}
      >
        <Typography
          variant="subtitle2"
          sx={{ color: COMMON_COLORS.text.secondary, fontWeight: 600 }}
        >
          Selected Items (drag to reorder priority)
        </Typography>
        <Typography variant="caption" sx={{ color: COMMON_COLORS.text.muted }}>
          Hunt
        </Typography>
      </Box>
      <Paper
        elevation={0}
        sx={{
          borderRadius: "12px",
          border: `1px solid ${themeColors.alpha.divider}`,
          background: themeColors.gradients.backgroundSubtle,
          p: 1,
        }}
      >
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
          <SortableContext
            items={selectedRows.map((r) => r.Name)}
            strategy={verticalListSortingStrategy}
          >
            {selectedRows.map((item, index) => (
              <SortableItem
                key={item.Name}
                item={item}
                index={index}
                huntItems={huntItems}
                onHuntToggle={onHuntToggle}
              />
            ))}
          </SortableContext>
        </DndContext>
      </Paper>
    </Box>
  );
}
