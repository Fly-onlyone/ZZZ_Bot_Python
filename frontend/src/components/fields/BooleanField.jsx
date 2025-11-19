import React from "react";
import { Switch } from "@mui/material";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * BooleanField Component
 *
 * Renders a Material-UI Switch for boolean values.
 * Themed according to the current theme context.
 */
export default function BooleanField({ id, value, onChange }) {
  const { themeColors } = useThemeContext();

  return (
    <Switch
      id={id}
      checked={value}
      onChange={(e) => onChange(e.target.checked)}
      className="ml-auto"
      sx={{
        "& .MuiSwitch-switchBase.Mui-checked": {
          color: themeColors.secondary.main,
        },
        "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
          backgroundColor: themeColors.secondary.main,
        },
      }}
    />
  );
}
