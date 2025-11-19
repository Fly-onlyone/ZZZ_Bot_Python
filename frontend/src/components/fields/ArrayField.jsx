import React from "react";
import { TimePicker } from "@mui/x-date-pickers";
import { Button } from "@mui/material";
import dayjs from "dayjs";
import { COMMON_COLORS } from "../../theme/colors";
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

  return (
    <div className="space-y-4">
      {value.map((time, index) => (
        <div
          key={index}
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
          <Button
            variant="contained"
            onClick={() => handleRemove(index)}
            sx={{
              background: COMMON_COLORS.error.main,
              color: "#ffffff",
              fontWeight: 600,
              "&:hover": {
                background: COMMON_COLORS.error.dark,
              },
            }}
          >
            Remove
          </Button>
        </div>
      ))}
      <Button
        variant="contained"
        onClick={handleAdd}
        sx={{
          background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
          color: "#ffffff",
          fontWeight: 600,
          "&:hover": {
            background: "linear-gradient(135deg, #059669 0%, #047857 100%)",
          },
        }}
      >
        Add Time
      </Button>
    </div>
  );
}
