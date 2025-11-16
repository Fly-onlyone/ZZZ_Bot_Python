import React from "react";
import { Alert, Box, Chip, Paper, Typography } from "@mui/material";
import { DataLoader } from "../DataLoader";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import LocalMallIcon from "@mui/icons-material/LocalMall";
import { DateTimeField } from "@mui/x-date-pickers";
import dayjs from "dayjs";

export default function Hunt() {
  const { useRouteData } = DataLoader();

  // Use the DataLoader's useRouteData hook
  const { data: huntInfo, error } = useRouteData("overview/hunt");

  if (error) {
    return (
      <Alert severity="error">Failed to fetch hunt data: {error.message}</Alert>
    );
  }

  if (!huntInfo) {
    return <Typography>Loading...</Typography>;
  }

  const { enabled, hunt_items, next_hunt_time } = huntInfo;

  // If hunt mode is disabled
  if (!enabled) {
    return (
      <Alert severity="info" sx={{ borderRadius: "12px" }}>
        Hunt mode is currently disabled. Enable it in Settings to start hunting
        for items.
      </Alert>
    );
  }

  // If hunt mode is enabled but no items
  if (!hunt_items || hunt_items.length === 0) {
    return (
      <Alert severity="warning" sx={{ borderRadius: "12px" }}>
        Hunt mode is enabled but no items are marked for hunting. Add items to
        hunt in the Shopping page.
      </Alert>
    );
  }

  return (
    <div>
      <Box
        sx={{ mb: 3, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}
      >
        <Paper
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background:
              "linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
          }}
        >
          <CheckCircleIcon sx={{ color: "#10b981", fontSize: 32 }} />
          <Typography
            variant="body1"
            sx={{ fontWeight: 600, color: "#34d399" }}
          >
            Hunt Mode Active
          </Typography>
        </Paper>
        <Paper
          elevation={2}
          sx={{
            p: 3,
            borderRadius: "12px",
            background:
              "linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%)",
            border: "1px solid rgba(245, 158, 11, 0.3)",
            textAlign: "center",
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: "#94a3b8", fontWeight: 600, mb: 1, display: "block" }}
          >
            Items Hunting
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 700, color: "#fbbf24" }}>
            {hunt_items.length}
          </Typography>
        </Paper>
      </Box>

      {next_hunt_time && (
        <Box
          sx={{
            mb: 3,
            p: 3,
            borderRadius: "12px",
            background:
              "linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)",
            border: "1px solid rgba(139, 92, 246, 0.2)",
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <AccessTimeIcon sx={{ color: "#8b5cf6", fontSize: 28 }} />
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, color: "#cbd5e1" }}>
              Next Hunt Scheduled:
            </Typography>
            <DateTimeField
              defaultValue={dayjs(next_hunt_time, "HH:mm DD/MM/YY")}
              format="DD/MM/YYYY - hh:mm A"
            />
          </Box>
        </Box>
      )}

      <Typography
        variant="h6"
        sx={{
          mb: 2,
          fontWeight: 600,
          color: "#cbd5e1",
        }}
      >
        Items Being Hunted
      </Typography>
      <Box
        sx={{
          borderRadius: "12px",
          overflow: "hidden",
          border: "1px solid rgba(139, 92, 246, 0.2)",
        }}
      >
        <Box
          component="table"
          sx={{
            width: "100%",
            borderCollapse: "collapse",
          }}
        >
          <Box
            component="thead"
            sx={{
              background:
                "linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%)",
            }}
          >
            <Box component="tr">
              <Box
                component="th"
                sx={{
                  px: 3,
                  py: 2,
                  textAlign: "left",
                  fontWeight: 600,
                  color: "#e2e8f0",
                  borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
                }}
              >
                #
              </Box>
              <Box
                component="th"
                sx={{
                  px: 3,
                  py: 2,
                  textAlign: "left",
                  fontWeight: 600,
                  color: "#e2e8f0",
                  borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
                }}
              >
                Item Name
              </Box>
              <Box
                component="th"
                sx={{
                  px: 3,
                  py: 2,
                  textAlign: "left",
                  fontWeight: 600,
                  color: "#e2e8f0",
                  borderBottom: "1px solid rgba(139, 92, 246, 0.2)",
                }}
              >
                Scheduled Hunt Time
              </Box>
            </Box>
          </Box>
          <Box component="tbody">
            {hunt_items.map((item, index) => (
              <Box
                component="tr"
                key={index}
                sx={{
                  background: "rgba(139, 92, 246, 0.05)",
                  transition: "all 0.2s ease-in-out",
                  "&:hover": {
                    background: "rgba(139, 92, 246, 0.12)",
                  },
                  borderBottom:
                    index !== hunt_items.length - 1
                      ? "1px solid rgba(139, 92, 246, 0.1)"
                      : "none",
                }}
              >
                <Box
                  component="td"
                  sx={{
                    px: 3,
                    py: 2,
                    color: "#94a3b8",
                    fontWeight: 600,
                  }}
                >
                  {index + 1}
                </Box>
                <Box
                  component="td"
                  sx={{
                    px: 3,
                    py: 2,
                    color: "#cbd5e1",
                    fontWeight: 500,
                  }}
                >
                  {item.name}
                </Box>
                <Box
                  component="td"
                  sx={{
                    px: 3,
                    py: 2,
                  }}
                >
                  <Chip
                    label={item.scheduled_time}
                    size="small"
                    icon={
                      item.scheduled_time !== "Not scheduled" &&
                      item.scheduled_time !== "Invalid time" ? (
                        <AccessTimeIcon sx={{ color: "#8b5cf6 !important" }} />
                      ) : null
                    }
                    sx={{
                      background:
                        item.scheduled_time === "Not scheduled" ||
                        item.scheduled_time === "Invalid time"
                          ? "rgba(107, 114, 128, 0.2)"
                          : "rgba(139, 92, 246, 0.2)",
                      color:
                        item.scheduled_time === "Not scheduled" ||
                        item.scheduled_time === "Invalid time"
                          ? "#9ca3af"
                          : "#a78bfa",
                      fontWeight: 600,
                      border: `1px solid ${
                        item.scheduled_time === "Not scheduled" ||
                        item.scheduled_time === "Invalid time"
                          ? "rgba(107, 114, 128, 0.3)"
                          : "rgba(139, 92, 246, 0.3)"
                      }`,
                    }}
                  />
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      </Box>
    </div>
  );
}
