import React, { useState } from "react";
import { IconButton, TextField as MuiTextField } from "@mui/material";
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
export default function TextField({ id, value, onChange, isPassword = false }) {
  const { themeColors } = useThemeContext();
  const [passwordVisible, setPasswordVisible] = useState(false);

  const togglePasswordVisibility = () => {
    setPasswordVisible((prev) => !prev);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(value || "");
  };

  return (
    <div className="flex flex-grow items-center gap-2">
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
      />
      {isPassword && (
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
          {passwordVisible ? <VisibilityOff /> : <Visibility />}
        </IconButton>
      )}
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
        <ContentCopy />
      </IconButton>
    </div>
  );
}
