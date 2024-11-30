import { Typography } from "@mui/material";
import Mission from "./content/Mission";

export default function Overview() {
  return (
    <div>
      <div className="relative flex flex-col items-center justify-center rounded-xl border-4 border-solid  border-teal-300 p-4">
        <Typography className=" mb-4 font-bold text-white" variant="h5">
          Mission Report
        </Typography>
        <Mission />
      </div>
      <div className="relative flex  flex-col  items-center rounded-xl border-4 border-solid border-teal-300">
        <Typography className="font-bold text-white" variant="h5">
          Desired Item
        </Typography>
      </div>
    </div>
  );
}
