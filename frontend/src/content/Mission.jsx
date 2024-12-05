import React, { useEffect } from "react";
import loginResults from "./../../../screenshot/login_reward.png";
import { Alert } from "@mui/material";

export default function Mission() {
  const [mission, setMission] = React.useState({});
  const BACKEND_URL = "http://127.0.0.1:8000";

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/overview/mission`);
        if (response.ok) {
          const data = await response.json();
          setMission(data);
        } else {
          console.log(`Failed to fetch data: ${response.statusText}`);
        }
      } catch {
        console.log("An error occurred while fetching data.");
      }
    };
    fetchData();
  }, []);
  const { day, check_in, missions } = mission;
  if (!missions) {
    return <Alert severity="error">Today task hasn't done yet</Alert>;
  }
  return (
    <div className="rounded-lg   p-6 shadow-md">
      <h1 className="mb-4 text-2xl font-bold text-green-600">Day : {day}</h1>
      <h2 className="mb-4 text-lg font-semibold">
        <strong>Check-in Status:</strong> {check_in}
      </h2>

      {check_in === "Login Success" && (
        <div className="my-4 flex justify-center">
          <img
            src={loginResults}
            alt="Login Reward"
            className="rounded-md shadow-md"
          />
        </div>
      )}

      <h2 className="mb-4 text-lg font-semibold">Mission Status:</h2>
      <table className="mb-6 w-full border-collapse">
        <thead>
          <tr>
            <th className="border border-gray-500 bg-gray-500 px-4 py-2 text-left">
              Mission
            </th>
            <th className="border border-gray-500 bg-gray-500 px-4 py-2 text-left">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {missions.map((mission, index) => (
            <tr
              key={index}
              className={`border border-gray-500 ${
                mission.state === "Finished" ? "bg-green-800" : "bg-red-800"
              }`}
            >
              <td className="px-4 py-2">{mission.name}</td>
              <td className="px-4 py-2">{mission.state}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
