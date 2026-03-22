import React from "react";
import { IconCards } from "@tabler/icons-react";
import { ValueAdapter } from "../components";
import { DataLoader } from "../services";

const monitoringTypeConfig = {
  sentry_traces_sample_rate: {
    type: "select",
    options: [
      { value: 1.0, label: "1.0 (Always)" },
      { value: 0.5, label: "0.5" },
      { value: 0.25, label: "0.25" },
      { value: 0.1, label: "0.1" },
    ],
  },
};

function formatCleanupSummary(report) {
  const deleted =
    report &&
    typeof report === "object" &&
    typeof report["deleted"] === "object"
      ? report["deleted"]
      : {};
  return (
    `Cleanup completed. Deleted ` +
    `${deleted["auth_storage_file"] || 0} auth file(s), ` +
    `${deleted["log_files"] || 0} log file(s), ` +
    `${deleted["screenshot_files"] || 0} screenshot file(s), ` +
    `${deleted["json_files"] || 0} JSON file(s).`
  );
}

export default function MonitoringPage() {
  const { useActionData } = DataLoader();
  const cleanupMutation = useActionData("maintenance/local-cleanup");

  const handleRunCleanup = async () => {
    return cleanupMutation.mutateAsync({});
  };

  return (
    <ValueAdapter
      route="settings"
      customSections={{
        Monitoring: {
          icon: <IconCards />,
          fields: [
            "sentry_dsn",
            "sentry_frontend_dsn",
            "sentry_send_test_event",
            "sentry_traces_sample_rate",
          ],
        },
      }}
      typeConfig={monitoringTypeConfig}
      extraActions={[
        {
          key: "run-local-cleanup",
          label: "Run Local Cleanup",
          onClick: handleRunCleanup,
          successMessage: formatCleanupSummary,
          errorMessage: "Failed to run local cleanup.",
        },
      ]}
    />
  );
}
