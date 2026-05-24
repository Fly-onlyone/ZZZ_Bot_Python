import { TimePicker } from "@mui/x-date-pickers";
import { Button } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import dayjs from "dayjs";
import { COMMON_COLORS } from "../../theme/colors";
import { GLOW } from "../../theme/styles";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * ArrayField Component
 *
 * Renders an array of time pickers with add/remove functionality.
 * Used for managing multiple time entries (e.g., schedule times).
 */
export default function ArrayField({ value = [], onChange }) {
  const { themeColors } = useThemeContext();

  const handleTimeChange = (index, newValue) => {
    const updatedArray = [...value];
    updatedArray[index] = newValue ? newValue.format("HH:mm") : "";
    onChange(updatedArray);
  };

  const handleRemove = (index) => {
    const updatedArray = value.filter((_, i) => i !== index);
    onChange(updatedArray);
  };

  const handleAdd = () => {
    onChange([...value, ""]);
  };

  // Animation variants
  const itemVariants = {
    hidden: { opacity: 0, y: -10, scale: 0.97 },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 200,
        damping: 20,
      },
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      transition: {
        duration: 0.15,
      },
    },
  };

  return (
    <div className="space-y-4">
      <AnimatePresence mode="popLayout">
        {value.map((time, index) => (
          <motion.div
            key={index}
            variants={itemVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            layout
            className="flex items-center justify-between gap-4 rounded-lg p-3"
            style={{
              background: themeColors.alpha.hover,
              border: `1px solid ${themeColors.alpha.cardBorder}`,
            }}
          >
            <TimePicker
              label="Select Time"
              value={time ? dayjs(time, "HH:mm") : null}
              onChange={(newValue) => handleTimeChange(index, newValue)}
            />
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Button
                variant="contained"
                onClick={() => handleRemove(index)}
                sx={{
                  background: `linear-gradient(135deg, ${COMMON_COLORS.error.main}CC 0%, ${COMMON_COLORS.error.dark}CC 100%)`,
                  color: "#ffffff",
                  fontWeight: 600,
                  boxShadow: GLOW.subtle("#EF4444"),
                  "&:hover": {
                    background: `linear-gradient(135deg, ${COMMON_COLORS.error.main} 0%, ${COMMON_COLORS.error.dark} 100%)`,
                    boxShadow: GLOW.medium("#EF4444"),
                    transform: "translateY(-2px)",
                  },
                }}
              >
                Remove
              </Button>
            </motion.div>
          </motion.div>
        ))}
      </AnimatePresence>
      <motion.div
        whileHover={{ y: -2 }}
        whileTap={{ y: 0, scale: 0.97 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        <Button
          variant="contained"
          onClick={handleAdd}
          sx={{
            background: `linear-gradient(135deg, ${COMMON_COLORS.success.main}CC 0%, ${COMMON_COLORS.success.dark}CC 100%)`,
            color: "#ffffff",
            fontWeight: 600,
            boxShadow: GLOW.subtle("#22C55E"),
            "&:hover": {
              background: `linear-gradient(135deg, ${COMMON_COLORS.success.main} 0%, ${COMMON_COLORS.success.dark} 100%)`,
              boxShadow: GLOW.medium("#22C55E"),
              transform: "translateY(-2px)",
            },
          }}
        >
          Add Time
        </Button>
      </motion.div>
    </div>
  );
}
