import { motion } from "framer-motion";
import Mission from "../content/Mission";
import CompactRunningStatus from "../content/CompactRunningStatus";
import { IconReportAnalytics } from "@tabler/icons-react";
import { SectionCard } from "../components";

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

export default function Overview() {
  return (
    <div className="space-y-6">
      <CompactRunningStatus />

      <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible">
        <SectionCard
          title="Mission Report"
          icon={<IconReportAnalytics size={24} color="#ffffff" />}
          colorScheme="primary"
        >
          <Mission />
        </SectionCard>
      </motion.div>
    </div>
  );
}
