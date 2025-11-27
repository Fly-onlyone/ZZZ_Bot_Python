import React from "react";
import { Switch } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * BooleanField Component
 *
 * Renders a Material-UI Switch for boolean values.
 * Themed according to the current theme context.
 */
export default function BooleanField({ id, value, onChange }) {
  const { themeColors } = useThemeContext();

  const switchVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
      },
    },
    hover: {
      scale: 1.1,
      transition: {
        duration: 0.2,
      },
    },
    tap: {
      scale: 0.95,
    },
  };

  return (
    <motion.div
      className="ml-auto"
      variants={switchVariants}
      initial="hidden"
      animate="visible"
      whileHover="hover"
      whileTap="tap"
    >
      <Switch
        id={id}
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        sx={{
          "& .MuiSwitch-switchBase.Mui-checked": {
            color: themeColors.secondary.main,
          },
          "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
            backgroundColor: themeColors.secondary.main,
          },
        }}
      />
    </motion.div>
  );
}
