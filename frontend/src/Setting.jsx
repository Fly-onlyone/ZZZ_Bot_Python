import React, {useState, useEffect} from "react";
import {TimePicker} from "@mui/x-date-pickers";
import {LocalizationProvider} from "@mui/x-date-pickers/LocalizationProvider";
import {TextField} from "@mui/material";
import {AdapterDayjs} from "@mui/x-date-pickers/AdapterDayjs";
import dayjs from "dayjs";

export default function Setting() {
    const [settings, setSettings] = useState({});
    const BACKEND_URL = "http://127.0.0.1:8000";
    
    // Fetch settings from the backend dynamically
    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const response = await fetch(`${BACKEND_URL}/settings`);
                if (response.ok) {
                    const data = await response.json();
                    setSettings(data); // Dynamically populate state
                } else {
                    console.error("Failed to fetch settings:", response.statusText);
                }
            } catch (error) {
                console.error("Error fetching settings:", error);
            }
        };

        fetchSettings();
    }, []);

    // Handle dynamic state changes
    const handleChange = (key, value) => {
        setSettings((prev) => ({
            ...prev,
            [key]: value,
        }));
    };

    // Handle form submission
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${BACKEND_URL}/settings`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(settings),
            });

            if (response.ok) {
                alert("Settings saved successfully!");
            } else {
                alert("Error saving settings.");
            }
        } catch (error) {
            console.error("Error saving settings:", error);
        }
    };

    // Render dynamic fields based on `settings` keys
    const renderFields = () => {
        return Object.keys(settings).map((key) => {
            const value = settings[key];

            // Render TimePicker for time-based settings
            if (Array.isArray(value)) {
                return (
                    <div key={key} className="mb-6">
                        <label className="block text-lg font-medium mb-2 capitalize">{key.replace(/_/g, " ")}:</label>
                        <div className="space-y-4">
                            {value.map((time, index) => (
                                <div
                                    key={index}
                                    className="flex items-center justify-between gap-4 bg-gray-700 p-3 rounded-lg"
                                >
                                    <TimePicker
                                        label="Select Time"
                                        value={time ? dayjs(time, "HH:mm") : null}
                                        onChange={(newValue) => {
                                            const updatedArray = [...value];
                                            updatedArray[index] = newValue ? newValue.format("HH:mm") : "";
                                            handleChange(key, updatedArray);
                                        }}
                                        renderInput={(params) => (
                                            <TextField
                                                {...params}
                                                fullWidth
                                                variant="outlined"
                                                size="small"
                                                sx={{
                                                    bgcolor: "white",
                                                    borderRadius: "5px",
                                                }}
                                            />
                                        )}
                                    />
                                    <button
                                        type="button"
                                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg"
                                        onClick={() => {
                                            const updatedArray = value.filter((_, i) => i !== index);
                                            handleChange(key, updatedArray);
                                        }}
                                    >
                                        Remove
                                    </button>
                                </div>
                            ))}
                            <button
                                type="button"
                                className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg"
                                onClick={() => handleChange(key, [...value, ""])}
                            >
                                Add Time
                            </button>
                        </div>
                    </div>
                );
            }

            // Render Checkbox for boolean values
            if (typeof value === "boolean") {
                return (
                    <div key={key} className="flex items-center space-x-2 mb-6">
                        <input
                            type="checkbox"
                            id={key}
                            name={key}
                            className="w-5 h-5"
                            checked={value}
                            onChange={(e) => handleChange(key, e.target.checked)}
                        />
                        <label htmlFor={key} className="font-medium text-lg capitalize">
                            {key.replace(/_/g, " ")}
                        </label>
                    </div>
                );
            }

            // Render Text Input for other types of values
            return (
                <div key={key} className="mb-6">
                    <label htmlFor={key} className="block text-lg font-medium mb-2 capitalize">
                        {key.replace(/_/g, " ")}:
                    </label>
                    <TextField
                        id={key}
                        value={value}
                        onChange={(e) => handleChange(key, e.target.value)}
                        fullWidth
                        variant="outlined"
                        size="small"
                        sx={{
                            bgcolor: "white",
                            borderRadius: "5px",
                        }}
                    />
                </div>
            );
        });
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <div className="bg-gray-900 text-white min-h-screen flex items-center justify-center">
                <div className="container mx-auto p-8 max-w-4xl bg-gray-800 rounded-lg shadow-lg">
                    <h1 className="text-4xl font-bold mb-6 text-center">ZZZ Bot Scheduler</h1>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {renderFields()}
                        <button
                            type="submit"
                            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg w-full text-lg"
                        >
                            Save Settings
                        </button>
                    </form>
                </div>
            </div>
        </LocalizationProvider>
    );
}