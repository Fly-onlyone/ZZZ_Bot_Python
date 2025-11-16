import React from "react";
import { Alert, Button, Snackbar } from "@mui/material";
import SaveIcon from "@mui/icons-material/Save";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { TRANSITIONS } from "./theme/styles";
import { useThemeContext } from "./theme/ThemeContext";

const SaveButton = ({ onSave, alert, setAlert }) => {
  const { themeColors } = useThemeContext();

  const handleCloseAlert = () => {
    setAlert({ ...alert, open: false });
  };

  // Choose your preferred style by uncommenting one:

  // STYLE 1: Glass Morphism (Elegant & Modern)
  const glassStyle = {
    mt: 2,
    px: 4,
    py: 1.5,
    background: `linear-gradient(135deg, ${themeColors.primary.main}22 0%, ${themeColors.secondary.main}22 100%)`,
    backdropFilter: "blur(10px)",
    border: `2px solid ${themeColors.primary.main}`,
    color: themeColors.primary.light,
    fontWeight: 600,
    borderRadius: "12px",
    boxShadow: `0 4px 15px ${themeColors.alpha.card}`,
    transition: TRANSITIONS.default,
    "&:hover": {
      background: `linear-gradient(135deg, ${themeColors.primary.main}33 0%, ${themeColors.secondary.main}33 100%)`,
      border: `2px solid ${themeColors.secondary.light}`,
      transform: "translateY(-2px)",
      boxShadow: `0 8px 25px ${themeColors.alpha.hover}`,
    },
  };

  // STYLE 2: Elevated Shadow (Bold & Professional)
  const elevatedStyle = {
    mt: 2,
    px: 4,
    py: 1.5,
    background: themeColors.gradients.primary,
    color: "#ffffff",
    fontWeight: 700,
    borderRadius: "12px",
    boxShadow: `0 8px 24px ${themeColors.alpha.hover}, 0 4px 8px ${themeColors.alpha.card}`,
    transition: TRANSITIONS.default,
    "&:hover": {
      background: themeColors.gradients.primaryLight,
      transform: "translateY(-3px) scale(1.02)",
      boxShadow: `0 12px 32px ${themeColors.alpha.hover}, 0 6px 12px ${themeColors.alpha.card}`,
    },
    "&:active": {
      transform: "translateY(-1px) scale(0.98)",
    },
  };

  // STYLE 3: Outlined with Fill Animation (Clean & Minimalist)
  const outlinedStyle = {
    mt: 2,
    px: 4,
    py: 1.5,
    background: "transparent",
    border: `2px solid ${themeColors.primary.main}`,
    color: themeColors.primary.main,
    fontWeight: 600,
    borderRadius: "10px",
    position: "relative",
    overflow: "hidden",
    transition: TRANSITIONS.default,
    "&::before": {
      content: '""',
      position: "absolute",
      top: 0,
      left: "-100%",
      width: "100%",
      height: "100%",
      background: themeColors.gradients.primary,
      transition: "left 0.4s ease",
      zIndex: -1,
    },
    "&:hover": {
      color: "#ffffff",
      border: `2px solid ${themeColors.secondary.light}`,
      transform: "translateY(-2px)",
      boxShadow: `0 6px 20px ${themeColors.alpha.hover}`,
      "&::before": {
        left: 0,
      },
    },
  };

  // STYLE 4: Pill with Icon Badge (Playful & Modern)
  const pillStyle = {
    mt: 2,
    px: 4,
    py: 1.5,
    background: themeColors.gradients.primary,
    color: "#ffffff",
    fontWeight: 600,
    borderRadius: "50px",
    boxShadow: `0 4px 15px ${themeColors.alpha.hover}`,
    transition: TRANSITIONS.default,
    "& .MuiButton-startIcon": {
      background: "rgba(255, 255, 255, 0.2)",
      borderRadius: "50%",
      padding: "6px",
      marginRight: "8px",
    },
    "&:hover": {
      background: themeColors.gradients.primaryLight,
      transform: "translateY(-2px) scale(1.05)",
      boxShadow: `0 8px 25px ${themeColors.alpha.hover}`,
      "& .MuiButton-startIcon": {
        background: "rgba(255, 255, 255, 0.3)",
        transform: "rotate(360deg)",
      },
    },
  };

  // STYLE 5: Neumorphic (Soft & Tactile)
  const neumorphicStyle = {
    mt: 2,
    px: 4,
    py: 1.5,
    background: themeColors.primary.dark,
    color: "#ffffff",
    fontWeight: 600,
    borderRadius: "15px",
    boxShadow: `8px 8px 16px ${themeColors.alpha.card}, -8px -8px 16px rgba(255, 255, 255, 0.05)`,
    transition: TRANSITIONS.default,
    "&:hover": {
      background: themeColors.primary.main,
      boxShadow: `4px 4px 8px ${themeColors.alpha.card}, -4px -4px 8px rgba(255, 255, 255, 0.05)`,
      transform: "scale(0.98)",
    },
    "&:active": {
      boxShadow: `inset 4px 4px 8px ${themeColors.alpha.card}, inset -4px -4px 8px rgba(255, 255, 255, 0.05)`,
    },
  };

  // STYLE 6: Neon Glow (Vibrant & Eye-catching)
  const neonStyle = {
    mt: 2,
    px: 4,
    py: 1.5,
    background: "transparent",
    border: `2px solid ${themeColors.primary.main}`,
    color: themeColors.primary.light,
    fontWeight: 700,
    borderRadius: "8px",
    textShadow: `0 0 10px ${themeColors.primary.light}`,
    boxShadow: `0 0 10px ${themeColors.primary.main}, inset 0 0 10px ${themeColors.alpha.card}`,
    transition: TRANSITIONS.default,
    "&:hover": {
      background: themeColors.primary.main,
      color: "#ffffff",
      border: `2px solid ${themeColors.secondary.light}`,
      textShadow: "none",
      boxShadow: `0 0 20px ${themeColors.secondary.main}, 0 0 40px ${themeColors.secondary.main}, inset 0 0 20px ${themeColors.alpha.hover}`,
      transform: "translateY(-2px)",
    },
  };

  // Select which style to use (change this variable)
  const selectedStyle = neonStyle; // Try: glassStyle, elevatedStyle, outlinedStyle, pillStyle, neumorphicStyle, neonStyle

  return (
    <>
      <div style={{ display: "flex", justifyContent: "center", marginTop: "2rem" }}>
        <Button
          variant="contained"
          onClick={onSave}
          startIcon={<SaveIcon />}
          sx={selectedStyle}
        >
          Save
        </Button>
      </div>

      <Snackbar
        open={alert.open}
        autoHideDuration={3000}
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={alert.type} variant="outlined">
          {alert.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default SaveButton;
