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

export default function LogsSkeleton() {
  const { themeColors } = useThemeContext();

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants}>
      <Paper
        component={motion.div}
        variants={itemVariants}
        elevation={0}
        sx={{
          borderRadius: "16px",
          background: themeColors.gradients.backgroundSubtle,
          border: `1px solid ${themeColors.alpha.cardBorder}`,
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            background: themeColors.gradients.header,
            borderBottom: `1px solid ${themeColors.alpha.cardBorder}`,
            p: "20px 24px",
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <Skeleton variant="rounded" width={44} height={44} />
          <Skeleton variant="text" width={60} height={32} />
        </Box>

        <Box sx={{ p: 3 }}>
          {/* Filter bar */}
          <Box
            component={motion.div}
            variants={itemVariants}
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 2,
              mb: 2,
              alignItems: "center",
            }}
          >
            <Skeleton variant="rounded" width={180} height={40} />
            <Box sx={{ display: "flex", gap: 0.5 }}>
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} variant="rounded" width={60} height={24} />
              ))}
            </Box>
            <Skeleton
              variant="rounded"
              width={200}
              height={40}
              sx={{ ml: "auto" }}
            />
          </Box>

          {/* Stats chips */}
          <Box
            component={motion.div}
            variants={itemVariants}
            sx={{ display: "flex", gap: 1, mb: 2 }}
          >
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} variant="rounded" width={70} height={24} />
            ))}
            <Skeleton variant="text" width={60} height={24} sx={{ ml: 1 }} />
          </Box>

          {/* Table */}
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
                <Skeleton variant="text" width="20%" height={24} />
                <Skeleton variant="text" width="10%" height={24} />
                <Skeleton variant="text" width="15%" height={24} />
                <Skeleton variant="text" width="45%" height={24} />
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
                <Skeleton variant="text" width="20%" height={20} />
                <Skeleton variant="rounded" width={50} height={20} />
                <Skeleton variant="text" width="15%" height={20} />
                <Skeleton variant="text" width="45%" height={20} />
              </Box>
            ))}
          </Box>
        </Box>
      </Paper>
    </motion.div>
  );
}
