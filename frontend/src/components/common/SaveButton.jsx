import React from "react";
import { Alert, Button, Snackbar } from "@mui/material";
import { motion } from "framer-motion";
import SaveIcon from "@mui/icons-material/Save";
import { TRANSITIONS } from "../../theme/styles";
import { useThemeContext } from "../../theme/ThemeContext";

const SaveButton = ({ onSave, alert, setAlert }) => {
  const { themeColors } = useThemeContext();

  const handleCloseAlert = () => {
    setAlert({ ...alert, open: false });
  };

  // Animation variants
  const buttonVariants = {
    initial: { scale: 1 },
    hover: { scale: 1.05 },
    tap: { scale: 0.95 },
  };

  const iconVariants = {
    hover: {
      rotate: [0, -10, 10, -10, 0],
      transition: { duration: 0.5 },
    },
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
    px: 3,
    py: 1.2,
    background: "rgba(15, 23, 42, 0.4)",
    border: `1px solid ${themeColors.primary.main}60`, // Even softer border
    color: themeColors.primary.main,
    fontWeight: 600,
    borderRadius: "8px",
    position: "relative",
    backdropFilter: "blur(10px)",
    // Minimal initial shadow
    boxShadow: `0 0 5px ${themeColors.primary.main}10`,
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    "&::before": {
      content: '""',
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      borderRadius: "8px",
      // Very subtle hover glow
      boxShadow: `0 0 10px ${themeColors.primary.main}20`,
      opacity: 0,
      transition: "opacity 0.3s ease",
    },
    "&:hover": {
      background: `${themeColors.primary.main}40`, // 40% opacity instead of solid
      color: themeColors.primary.light, // Use light primary instead of pure white
      border: `1px solid ${themeColors.primary.main}`,
      transform: "translateY(-1px)",
      // dim hover shadow
      boxShadow: `
        0 2px 10px ${themeColors.primary.main}10,
        0 1px 5px ${themeColors.primary.main}05
      `,
      "&::before": {
        opacity: 0.5, // Reduced opacity
      },
      "& .MuiButton-startIcon": {
        color: themeColors.primary.light,
      },
    },
    "&:active": {
      transform: "scale(0.99)",
      boxShadow: `0 0 5px ${themeColors.primary.main}10`,
    },
  };

  // Select which style to use (change this variable)
  const selectedStyle = neonStyle; // Try: glassStyle, elevatedStyle, outlinedStyle, pillStyle, neumorphicStyle, neonStyle

  return (
    <>
      <div
        style={{ display: "flex", justifyContent: "center", marginTop: "2rem" }}
      >
        <motion.div
          variants={buttonVariants}
          initial="initial"
          whileHover="hover"
          whileTap="tap"
        >
          <Button
            variant="contained"
            onClick={onSave}
            startIcon={
              <motion.div
                variants={iconVariants}
                whileHover="hover"
                style={{ display: "flex", alignItems: "center" }}
              >
                <SaveIcon />
              </motion.div>
            }
            sx={selectedStyle}
          >
            Save
          </Button>
        </motion.div>
      </div>

      <Snackbar
        open={alert.open}
        autoHideDuration={3000}
        onClose={handleCloseAlert}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          transition={{ duration: 0.3 }}
        >
          <Alert severity={alert.type} variant="outlined">
            {alert.message}
          </Alert>
        </motion.div>
      </Snackbar>
    </>
  );
};

export default SaveButton;
