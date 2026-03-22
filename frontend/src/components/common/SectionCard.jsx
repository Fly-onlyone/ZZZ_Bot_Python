import React, { memo } from "react";
import { Box, Paper, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../theme/ThemeContext";
import { COMMON_COLORS } from "../../theme/colors";
import { GLOW } from "../../theme/styles";

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
  hover: {
    scale: 1.1,
    rotate: 5,
    transition: {
      duration: 0.3,
      ease: "easeOut",
    },
  },
};

// Memoized icon badge component (decorative)
const IconBadge = memo(({ icon, gradient, themeColors }) => (
  <motion.div
    variants={iconVariants}
    initial="hidden"
    animate="visible"
    whileHover="hover"
    aria-hidden="true"
  >
    <Box
      sx={{
        width: 44,
        height: 44,
        borderRadius: "12px",
        background: gradient,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: GLOW.subtle(themeColors.glow),
        border: `1px solid ${themeColors.alpha.divider}`,
      }}
    >
      {icon}
    </Box>
  </motion.div>
));

export default function SectionCard({
  title,
  icon,
  children,
  colorScheme = "primary",
  sx = {},
  contentSx = {},
  disableHover = false,
}) {
  const { themeColors } = useThemeContext();
  const isPrimary = colorScheme === "primary";

  // Dynamic values based on theme
  const cardBg = themeColors.gradients.backgroundSubtle;
  const headerBg = themeColors.gradients.header;
  const borderColor = themeColors.alpha.cardBorder;
  const iconGradient = isPrimary
    ? themeColors.gradients.primary
    : themeColors.gradients.primaryLight;

  return (
    <Paper
      component={motion.div}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={
        disableHover
          ? undefined
          : {
              y: -5,
              scale: 1.02,
              transition: { duration: 0.2, ease: "easeOut" },
            }
      }
      elevation={0}
      role="region"
      aria-label={title}
      sx={{
        borderRadius: "16px",
        background: cardBg,
        border: `1px solid ${borderColor}`,
        overflow: "hidden",
        backdropFilter: "blur(16px)",
        cursor: "default",
        position: "relative",
        "&:hover": {
          boxShadow: GLOW.medium(themeColors.glow),
          border: `1px solid ${themeColors.primary.main}60`,
        },
        ...sx,
      }}
    >
      <Box
        sx={{
          background: headerBg,
          borderBottom: `1px solid ${borderColor}`,
          padding: "20px 24px",
          display: "flex",
          alignItems: "center",
          gap: 2,
        }}
      >
        <IconBadge
          icon={icon}
          gradient={iconGradient}
          themeColors={themeColors}
        />
        <Typography
          variant="h5"
          sx={{
            fontWeight: 700,
            color: COMMON_COLORS.text.primary,
            fontFamily: '"Outfit", sans-serif',
            textShadow: GLOW.text(themeColors.glow),
          }}
        >
          {title}
        </Typography>
      </Box>
      <Box sx={{ padding: "24px", ...contentSx }}>{children}</Box>
    </Paper>
  );
}
