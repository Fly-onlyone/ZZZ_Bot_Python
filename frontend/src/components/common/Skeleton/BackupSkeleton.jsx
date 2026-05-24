import { Box, Paper, Skeleton } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../../theme/ThemeContext";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 },
  },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring", stiffness: 100, damping: 15 },
  },
};

function SectionCardShell({ children }) {
  const { themeColors } = useThemeContext();

  return (
    <Paper
      component={motion.div}
      variants={cardVariants}
      elevation={0}
      sx={{
        borderRadius: "16px",
        background: themeColors.gradients.backgroundSubtle,
        border: `1px solid ${themeColors.alpha.cardBorder}`,
        backdropFilter: "blur(8px)",
        overflow: "hidden",
      }}
    >
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
        <Skeleton variant="text" width={100} height={32} />
      </Box>
      <Box sx={{ p: 3 }}>{children}</Box>
    </Paper>
  );
}

export default function BackupSkeleton() {
  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Data Summary shell */}
      <SectionCardShell>
        {[1, 2, 3, 4].map((i) => (
          <Box
            key={i}
            sx={{
              display: "flex",
              justifyContent: "space-between",
              py: 1.5,
            }}
          >
            <Skeleton variant="text" width="25%" height={24} />
            <Skeleton variant="rounded" width={70} height={24} />
            <Skeleton variant="text" width="20%" height={24} />
          </Box>
        ))}
      </SectionCardShell>

      {/* Export shell */}
      <SectionCardShell>
        <Skeleton variant="text" width="60%" height={20} sx={{ mb: 2 }} />
        <Box sx={{ display: "flex", gap: 1.5, mb: 2 }}>
          <Skeleton variant="rounded" width={120} height={36} />
          <Skeleton variant="text" width="40%" height={24} />
        </Box>
        <Skeleton variant="rounded" width={140} height={36} />
      </SectionCardShell>

      {/* Restore shell */}
      <SectionCardShell>
        <Skeleton variant="text" width="70%" height={20} sx={{ mb: 2 }} />
        <Skeleton variant="rounded" width={160} height={36} />
      </SectionCardShell>
    </motion.div>
  );
}
