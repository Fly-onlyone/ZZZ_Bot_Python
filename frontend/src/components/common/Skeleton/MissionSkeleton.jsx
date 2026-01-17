import React from "react";
import { Box, Paper, Skeleton } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../../theme/ThemeContext";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
};

export default function MissionSkeleton() {
  const { themeColors } = useThemeContext();

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants}>
      {/* Stats cards */}
      <Box
        sx={{ mb: 3, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}
      >
        <Paper
          component={motion.div}
          variants={itemVariants}
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background: themeColors.gradients.backgroundSubtle,
            border: `1px solid ${themeColors.alpha.cardBorder}`,
            textAlign: "center",
          }}
        >
          <Skeleton
            variant="text"
            width={80}
            height={20}
            sx={{ mx: "auto", mb: 1 }}
          />
          <Skeleton variant="text" width={60} height={40} sx={{ mx: "auto" }} />
        </Paper>
        <Paper
          component={motion.div}
          variants={itemVariants}
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background: themeColors.gradients.backgroundSubtle,
            border: `1px solid ${themeColors.alpha.cardBorder}`,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
          }}
        >
          <Skeleton variant="circular" width={32} height={32} />
          <Skeleton variant="text" width={100} height={24} />
        </Paper>
      </Box>

      {/* Table skeleton */}
      <Skeleton variant="text" width={120} height={28} sx={{ mb: 2 }} />
      <Box
        sx={{
          borderRadius: "12px",
          overflow: "hidden",
          border: `1px solid ${themeColors.alpha.divider}`,
        }}
      >
        <Box sx={{ background: themeColors.gradients.header, p: 2 }}>
          <Box sx={{ display: "flex", gap: 2 }}>
            <Skeleton variant="text" width="60%" height={24} />
            <Skeleton variant="text" width="30%" height={24} />
          </Box>
        </Box>
        {[1, 2, 3].map((i) => (
          <Box
            key={i}
            component={motion.div}
            variants={itemVariants}
            sx={{
              p: 2,
              display: "flex",
              gap: 2,
              borderBottom:
                i !== 3 ? `1px solid ${themeColors.alpha.card}` : "none",
            }}
          >
            <Skeleton variant="text" width="60%" height={24} />
            <Skeleton variant="rounded" width={80} height={24} />
          </Box>
        ))}
      </Box>
    </motion.div>
  );
}
