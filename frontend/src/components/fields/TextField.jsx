import React, { useState } from "react";
import { IconButton, TextField as MuiTextField } from "@mui/material";
import { motion } from "framer-motion";
import { ContentCopy, Visibility, VisibilityOff } from "@mui/icons-material";
import { COMMON_COLORS } from "../../theme/colors";
import { TRANSITIONS } from "../../theme/styles";
import { useThemeContext } from "../../theme/ThemeContext";

/**
 * TextField Component
 *
 * Enhanced text field with optional password visibility toggle and copy-to-clipboard functionality.
 * Automatically handles password fields with show/hide toggle.
 */
export default function TextField({ id, value, onChange, isPassword = false, sx = {} }) {
  const { themeColors } = useThemeContext();
  const [passwordVisible, setPasswordVisible] = useState(false);

  const togglePasswordVisibility = () => {
    setPasswordVisible((prev) => !prev);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(value || "");
  };

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

  const buttonVariants = {
    hover: { scale: 1.1 },
    tap: { scale: 0.9 },
  };

  const iconVariants = {
    hover: { rotate: 15 },
  };

  return (
    <motion.div
      className="flex flex-grow items-center gap-2"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <MuiTextField
        className={isPassword ? "" : "pr-12"}
        id={id}
        type={
          isPassword && passwordVisible
            ? "text"
            : isPassword
            ? "password"
            : "text"
        }
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        fullWidth
        sx={sx}
      />
      {isPassword && (
        <motion.div variants={buttonVariants} whileHover="hover" whileTap="tap">
          <IconButton
            onClick={togglePasswordVisibility}
            title={passwordVisible ? "Hide" : "Show"}
            sx={{
              color: COMMON_COLORS.text.muted,
              transition: TRANSITIONS.default,
              "&:hover": {
                color: themeColors.secondary.main,
                backgroundColor: themeColors.alpha.hover,
              },
            }}
          >
            <motion.div variants={iconVariants} whileHover="hover">
              {passwordVisible ? <VisibilityOff /> : <Visibility />}
            </motion.div>
          </IconButton>
        </motion.div>
      )}
      <motion.div variants={buttonVariants} whileHover="hover" whileTap="tap">
        <IconButton
          onClick={handleCopy}
          title="Copy to clipboard"
          sx={{
            color: COMMON_COLORS.text.muted,
            transition: TRANSITIONS.default,
            "&:hover": {
              color: themeColors.secondary.main,
              backgroundColor: themeColors.alpha.hover,
            },
          }}
        >
          <motion.div variants={iconVariants} whileHover="hover">
            <ContentCopy />
          </motion.div>
        </IconButton>
      </motion.div>
    </motion.div>
  );
}
