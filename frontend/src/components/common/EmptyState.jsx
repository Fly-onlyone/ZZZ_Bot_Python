import React from "react";
import { Box, Button, Paper, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../theme/ThemeContext";
import { COMMON_COLORS } from "../../theme/colors";

const containerVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
};

const iconVariants = {
  hidden: { scale: 0, rotate: -180 },
  visible: {
    scale: 1,
    rotate: 0,
    transition: {
      type: "spring",
      stiffness: 200,
      damping: 15,
      delay: 0.2,
    },
  },
};

export default function EmptyState({
  icon,
  title,
  subtitle,
  action,
  actionLabel,
}) {
  const { themeColors } = useThemeContext();

  return (
    <Paper
      component={motion.div}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      elevation={0}
      sx={{
        borderRadius: "16px",
        background: themeColors.gradients.backgroundSubtle,
        border: `1px solid ${themeColors.alpha.cardBorder}`,
        overflow: "hidden",
        backdropFilter: "blur(12px)",
        py: 6,
        px: 4,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 2,
      }}
    >
      {icon && (
        <Box
          component={motion.div}
          variants={iconVariants}
          initial="hidden"
          animate="visible"
          sx={{
            width: 56,
            height: 56,
            borderRadius: "16px",
            background: themeColors.gradients.primary,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: `0 4px 14px ${themeColors.alpha.hover}`,
            border: `1px solid ${themeColors.alpha.divider}`,
            color: COMMON_COLORS.text.primary,
            filter: `drop-shadow(0 0 8px ${themeColors.glow}40)`,
            "& .MuiSvgIcon-root": { fontSize: 28 },
          }}
        >
          {icon}
        </Box>
      )}
      <Typography
        variant="h6"
        sx={{
          fontWeight: 700,
          color: COMMON_COLORS.text.primary,
          fontFamily: '"Outfit", sans-serif',
          textAlign: "center",
        }}
      >
        {title}
      </Typography>
      {subtitle && (
        <Typography
          variant="body2"
          sx={{
            color: COMMON_COLORS.text.muted,
            textAlign: "center",
            maxWidth: 360,
          }}
        >
          {subtitle}
        </Typography>
      )}
      {action && actionLabel && (
        <Button
          variant="outlined"
          onClick={action}
          sx={{
            mt: 1,
            borderColor: themeColors.primary.main,
            color: themeColors.primary.light,
            "&:hover": {
              borderColor: themeColors.primary.light,
              background: `${themeColors.primary.main}1A`,
            },
          }}
        >
          {actionLabel}
        </Button>
      )}
    </Paper>
  );
}
