import { IconCards } from "@tabler/icons-react";
import { ValueAdapter } from "../components";

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

export default function MonitoringPage() {
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
    />
  );
}
