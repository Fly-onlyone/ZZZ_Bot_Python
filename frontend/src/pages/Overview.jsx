import React, { memo } from "react";
import { Box, Paper, Typography } from "@mui/material";
import { motion } from "framer-motion";
import Mission from "../content/Mission";
import RunningStatus from "../content/RunningStatus";
import Hunt from "../content/Hunt";
import {
  IconActivity,
  IconReportAnalytics,
  IconTarget,
} from "@tabler/icons-react";
import { COMMON_COLORS } from "../theme/colors";
import { TRANSITIONS } from "../theme/styles";
import { useThemeContext } from "../theme/ThemeContext";

/**
 * Animation variants for staggered card animations
 */
const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      delay: i * 0.1,
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1],
    },
  }),
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
  hover: {
    scale: 1.1,
    rotate: 5,
    transition: {
      duration: 0.3,
      ease: "easeOut",
    },
  },
};

// Memoized icon badge component to prevent unnecessary re-renders
const IconBadge = memo(({ icon, gradient, themeColors }) => (
  <motion.div
    variants={iconVariants}
    initial="hidden"
    animate="visible"
    whileHover="hover"
  >
    <Box
      sx={{
        width: 40,
        height: 40,
        borderRadius: "10px",
        background: gradient,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: `0 4px 14px ${themeColors.alpha.hover}`,
      }}
    >
      {icon}
    </Box>
  </motion.div>
));

export default function Overview() {
  const { themeColors } = useThemeContext();

  // Section card component
  const SectionCard = ({ title, icon, children, colorScheme = "primary" }) => {
    const isPrimary = colorScheme === "primary";
    // Use theme colors for both primary and success color schemes
    const cardBg = themeColors.gradients.backgroundSubtle;
    const headerBg = themeColors.gradients.header;
    const borderColor = themeColors.alpha.cardBorder;
    const iconGradient = isPrimary
      ? themeColors.gradients.primary
      : themeColors.gradients.primaryLight;

    return (
      <Paper
        elevation={0}
        sx={{
          borderRadius: "16px",
          background: cardBg,
          border: `1px solid ${borderColor}`,
          overflow: "hidden",
          transition: TRANSITIONS.default,
          "&:hover": {
            boxShadow: `0 8px 32px ${themeColors.alpha.hover}`,
            transform: "translateY(-2px)",
          },
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
            sx={{ fontWeight: 700, color: COMMON_COLORS.text.primary }}
          >
            {title}
          </Typography>
        </Box>
        <Box sx={{ padding: "24px" }}>{children}</Box>
      </Paper>
    );
  };

  return (
    <div className="space-y-6">
      <motion.div
        custom={0}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <SectionCard
          title="Mission Report"
          icon={<IconReportAnalytics size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <Mission />
        </SectionCard>
      </motion.div>

      <motion.div
        custom={1}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <SectionCard
          title="Hunt Mode"
          icon={<IconTarget size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <Hunt />
        </SectionCard>
      </motion.div>

      <motion.div
        custom={2}
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        <SectionCard
          title="Running Status"
          icon={<IconActivity size={24} color="#ffffff" />}
          colorScheme="success"
        >
          <RunningStatus />
        </SectionCard>
      </motion.div>
    </div>
  );
}
