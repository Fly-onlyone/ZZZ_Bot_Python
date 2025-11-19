import React from "react";
import { FormControl, MenuItem, Select } from "@mui/material";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * SelectField Component
 *
 * Renders a Material-UI Select dropdown with custom theming.
 * Used for fields with predefined options (e.g., theme selection).
 */
export default function SelectField({ id, value, options = [], onChange }) {
  const { themeColors } = useThemeContext();

  return (
    <FormControl fullWidth>
      <Select
        id={id}
        value={value || options[0]?.value || ""}
        onChange={(e) => onChange(e.target.value)}
        sx={{
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.primary.main,
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.main,
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.light,
          },
        }}
      >
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
