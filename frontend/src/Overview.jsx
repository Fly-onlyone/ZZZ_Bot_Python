import { Typography } from "@mui/material";
import Mission from "./content/Mission";
import RunningStatus from "./content/RunningStatus";

export default function Overview() {
  return (
    <div className="space-y-6">
      <div className=" rounded-xl border-4 border-solid  border-teal-300 ">
        <Typography
          className="relative mb-4 flex flex-col items-center justify-center pt-10 font-bold text-white"
          variant="h5"
        >
          Mission Report
        </Typography>
        <Mission />
      </div>
      <div className=" rounded-xl border-4 border-solid  border-teal-300 ">
        <Typography
          className="relative mb-4 flex flex-col items-center justify-center p-4 font-bold text-white"
          variant="h5"
        >
          Running status
          <RunningStatus />
        </Typography>
      </div>
    </div>
  );
}
