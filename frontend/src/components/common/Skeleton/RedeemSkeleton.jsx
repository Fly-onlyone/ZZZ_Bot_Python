import React from "react";
import { Box, Skeleton } from "@mui/material";
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

export default function RedeemSkeleton() {
  const { themeColors } = useThemeContext();

  return (
    <motion.div initial="hidden" animate="visible" variants={containerVariants}>
      <Box
        component={motion.div}
        variants={itemVariants}
        sx={{
          height: 420,
          width: "100%",
          borderRadius: "12px",
          overflow: "hidden",
          border: `1px solid ${themeColors.alpha.divider}`,
        }}
      >
        {/* Header row */}
        <Box sx={{ background: themeColors.gradients.header, p: 2 }}>
          <Box sx={{ display: "flex", gap: 2 }}>
            <Skeleton variant="text" width="8%" height={24} />
            <Skeleton variant="text" width="20%" height={24} />
            <Skeleton variant="text" width="20%" height={24} />
            <Skeleton variant="text" width="15%" height={24} />
            <Skeleton variant="text" width="10%" height={24} />
            <Skeleton variant="text" width="12%" height={24} />
          </Box>
        </Box>

        {/* Data rows */}
        {[1, 2, 3, 4].map((i) => (
          <Box
            key={i}
            component={motion.div}
            variants={itemVariants}
            sx={{
              p: 2,
              display: "flex",
              gap: 2,
              borderBottom:
                i !== 4 ? `1px solid ${themeColors.alpha.card}` : "none",
            }}
          >
            <Skeleton variant="text" width="8%" height={24} />
            <Skeleton variant="text" width="20%" height={24} />
            <Skeleton variant="text" width="20%" height={24} />
            <Skeleton variant="text" width="15%" height={24} />
            <Skeleton variant="circular" width={24} height={24} />
            <Skeleton variant="rounded" width={60} height={32} />
          </Box>
        ))}
      </Box>
    </motion.div>
  );
}
