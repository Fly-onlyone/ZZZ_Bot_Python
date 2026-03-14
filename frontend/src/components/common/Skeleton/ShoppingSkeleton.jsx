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

export default function ShoppingSkeleton() {
  const { themeColors } = useThemeContext();

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants}>
      <Box sx={{ p: 4 }}>
        {/* Header row */}
        <Box
          component={motion.div}
          variants={itemVariants}
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 2,
          }}
        >
          <Skeleton variant="text" width={120} height={32} />
          <Skeleton variant="text" width={200} height={32} />
        </Box>

        {/* Sortable items */}
        <Paper
          component={motion.div}
          variants={itemVariants}
          elevation={0}
          sx={{
            p: 2,
            mb: 3,
            borderRadius: "12px",
            background: themeColors.gradients.backgroundSubtle,
            border: `1px solid ${themeColors.alpha.cardBorder}`,
          }}
        >
          {[1, 2, 3].map((i) => (
            <Box
              key={i}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 2,
                py: 1,
                borderBottom:
                  i !== 3 ? `1px solid ${themeColors.alpha.divider}` : "none",
              }}
            >
              <Skeleton variant="circular" width={24} height={24} />
              <Skeleton variant="text" width="40%" height={24} />
              <Box sx={{ ml: "auto" }}>
                <Skeleton variant="rounded" width={60} height={24} />
              </Box>
            </Box>
          ))}
        </Paper>

        {/* DataGrid placeholder */}
        <Box
          component={motion.div}
          variants={itemVariants}
          sx={{
            borderRadius: "12px",
            overflow: "hidden",
            border: `1px solid ${themeColors.alpha.divider}`,
          }}
        >
          <Box sx={{ background: themeColors.gradients.header, p: 2 }}>
            <Box sx={{ display: "flex", gap: 2 }}>
              <Skeleton variant="text" width="30%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
            </Box>
          </Box>
          {[1, 2, 3, 4, 5].map((i) => (
            <Box
              key={i}
              component={motion.div}
              variants={itemVariants}
              sx={{
                p: 2,
                display: "flex",
                gap: 2,
                borderBottom:
                  i !== 5 ? `1px solid ${themeColors.alpha.card}` : "none",
              }}
            >
              <Skeleton variant="rounded" width={20} height={20} />
              <Skeleton variant="text" width="30%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
              <Skeleton variant="text" width="15%" height={24} />
            </Box>
          ))}
        </Box>
      </Box>
    </motion.div>
  );
}
