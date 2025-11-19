import { BACKEND_URL, DataLoader } from "../services/DataLoader";
import { Alert, Typography } from "@mui/material";
import React from "react";
import { DateTimeField } from "@mui/x-date-pickers";
import dayjs from "dayjs";

export default function RunningStatus() {
  const { useRouteData } = DataLoader();
  const { data, error } = useRouteData("check-run-status");
  if (error) {
    return (
      <Alert severity="error">
        Failed to fetch mission data: {error.message}
      </Alert>
    );
  }
  if (!data) {
    return <Typography>Loading...</Typography>;
  }
  const { last_run, next_run } = data;
  return (
    <div className="space-x-8 pt-6">
      <div className="flex flex-row items-center justify-center gap-6">
        <img src={`${BACKEND_URL}/images/Zhu Yuan02.ico`} />
        <Typography className="mb-2 font-semibold text-orange-500" variant="h6">
          Last run
        </Typography>
        <DateTimeField
          defaultValue={dayjs(last_run, "HH:mm DD/MM/YY")}
          format={"DD/MM/YYYY - hh:mm A"}
        />
        <Typography className="mb-2 font-semibold text-red-500" variant="h6">
          Next run
        </Typography>
        <DateTimeField
          defaultValue={dayjs(next_run, "HH:mm DD/MM/YY")}
          format={"DD/MM/YYYY - hh:mm A"}
        />
      </div>
    </div>
  );
}
