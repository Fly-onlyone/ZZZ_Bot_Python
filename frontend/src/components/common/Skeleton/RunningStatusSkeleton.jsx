import React from "react";
import { Box, Skeleton } from "@mui/material";
import { motion } from "framer-motion";

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

export default function RunningStatusSkeleton() {
  return (
    <motion.div
      className="space-x-8 pt-6"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <Box
        component={motion.div}
        variants={containerVariants}
        sx={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "center",
          gap: 3,
          backdropFilter: "blur(8px)",
        }}
      >
        <motion.div variants={itemVariants}>
          <Skeleton variant="circular" width={48} height={48} />
        </motion.div>
        <motion.div variants={itemVariants}>
          <Skeleton variant="text" width={80} height={28} />
        </motion.div>
        <motion.div variants={itemVariants}>
          <Skeleton variant="rounded" width={200} height={40} />
        </motion.div>
        <motion.div variants={itemVariants}>
          <Skeleton variant="text" width={80} height={28} />
        </motion.div>
        <motion.div variants={itemVariants}>
          <Skeleton variant="rounded" width={200} height={40} />
        </motion.div>
      </Box>
    </motion.div>
  );
}
