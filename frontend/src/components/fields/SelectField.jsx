import React from "react";
import { FormControl, MenuItem, Select } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * SelectField Component
 *
 * Renders a Material-UI Select dropdown with custom theming and animations.
 * Used for fields with predefined options (e.g., theme selection).
 */
export default function SelectField({
  id,
  value,
  options = [],
  onChange,
  sx = {},
}) {
  const { themeColors } = useThemeContext();

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
      },
    },
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="visible">
      <FormControl fullWidth>
        <Select
          id={id}
          value={value || options[0]?.value || ""}
          onChange={(e) => onChange(e.target.value)}
          sx={sx}
        >
          {options.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </motion.div>
  );
}
