import React, { useMemo } from "react";
import { Alert, Button, CircularProgress, Snackbar } from "@mui/material";
import { keyframes } from "@mui/system";
import { motion } from "framer-motion";
import SaveIcon from "@mui/icons-material/Save";
import { useThemeContext } from "../../theme/ThemeContext";
import { GLOW } from "../../theme/styles";

const SaveButton = ({ onSave, alert, setAlert, loading = false }) => {
  const { themeColors, prefersReducedMotion } = useThemeContext();

  // Neon pulse animation - subtle breathing glow effect
  const neonPulse = useMemo(
    () => keyframes`
    0%, 100% {
      box-shadow:
        0 0 4px ${themeColors.glow}60,
        0 0 8px ${themeColors.glow}40;
    }
    50% {
      box-shadow:
        0 0 6px ${themeColors.glow}80,
        0 0 10px ${themeColors.glow}60;
    }
  `,
    [themeColors.glow]
  );

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

  // Neon Glow style
  const buttonStyle = {
    mt: 2,
    px: 4,
    py: 1.5,
    background: "transparent",
    border: `1px solid ${themeColors.primary.main}80`,
    color: themeColors.primary.light,
    fontWeight: 600,
    fontSize: "0.875rem",
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    borderRadius: "12px",
    backdropFilter: "blur(8px)",
    textShadow: `0 0 4px ${themeColors.primary.main}80`,
    boxShadow: `
      0 0 4px ${themeColors.primary.main}60,
      0 0 8px ${themeColors.primary.main}40
    `,
    animation: prefersReducedMotion
      ? "none"
      : `${neonPulse} 3s ease-in-out infinite`,
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    "&:hover": {
      background: `${themeColors.primary.main}15`,
      color: "#ffffff",
      border: `1px solid ${themeColors.primary.main}`,
      textShadow: `0 0 6px ${themeColors.primary.light}`,
      boxShadow: GLOW.strong(themeColors.glow),
      transform: "translateY(-2px)",
      animation: "none",
    },
    "&:active": {
      transform: "scale(0.98)",
      boxShadow: `0 0 4px ${themeColors.primary.main}60`,
    },
    "&.Mui-disabled": {
      opacity: 0.7,
      color: themeColors.primary.light,
    },
  };

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
            disabled={loading}
            startIcon={
              loading ? (
                <CircularProgress size={18} color="inherit" />
              ) : (
                <motion.div
                  variants={iconVariants}
                  whileHover="hover"
                  style={{ display: "flex", alignItems: "center" }}
                >
                  <SaveIcon />
                </motion.div>
              )
            }
            sx={buttonStyle}
          >
            {loading ? "Saving..." : "Save"}
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
