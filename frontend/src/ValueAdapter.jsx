import React, { useState } from "react";
import { TimePicker } from "@mui/x-date-pickers";
import {
  Button,
  Divider,
  FormControl,
  IconButton,
  MenuItem,
  Select,
  Switch,
  TextField,
} from "@mui/material";
import dayjs from "dayjs";
import { useLocation } from "react-router-dom";
import { ContentCopy, Visibility, VisibilityOff } from "@mui/icons-material";
import { useQueryClient } from "@tanstack/react-query";
import { DataLoader } from "./DataLoader";
import SaveButton from "./SaveButton";
import { COMMON_COLORS } from "./theme/colors";
import { TRANSITIONS } from "./theme/styles";
import { useThemeContext } from "./theme/ThemeContext";

export default function ValueAdapter({
  customIcons = {},
  customSections = null,
  typeConfig = {},
}) {
  const { themeColors } = useThemeContext();
  const [alert, setAlert] = useState({
    open: false,
    type: "success",
    message: "",
  });
  const [passwordVisibility, setPasswordVisibility] = useState({});
  const location = useLocation();
  const route = location.pathname.replace("/", "");

  const { useRouteData, useSaveData } = DataLoader();

  const { data: value = {}, error } = useRouteData(route);
  const mutation = useSaveData(route);

  const queryClient = useQueryClient();

  const handleChange = (key, newValue) => {
    queryClient.setQueryData([route], (prev) => ({
      ...prev,
      [key]: newValue,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(value, {
      onSuccess: () => {
        setAlert({
          open: true,
          type: "success",
          message: "Data saved successfully!",
        });
      },
      onError: () => {
        setAlert({
          open: true,
          type: "error",
          message: "Failed to save data.",
        });
      },
    });
  };
  const togglePasswordVisibility = (key) => {
    setPasswordVisibility((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  // Render array field (time pickers)
  const renderArrayField = (key, fieldValue) => (
    <div className="space-y-4">
      {fieldValue.map((time, index) => (
        <div
          key={index}
          className="flex items-center justify-between gap-4 rounded-lg p-3"
          style={{
            background: themeColors.alpha.hover,
            border: `1px solid ${themeColors.alpha.cardBorder}`,
          }}
        >
          <TimePicker
            label="Select Time"
            value={time ? dayjs(time, "HH:mm") : null}
            onChange={(newValue) => {
              const updatedArray = [...fieldValue];
              updatedArray[index] = newValue ? newValue.format("HH:mm") : "";
              handleChange(key, updatedArray);
            }}
          />
          <Button
            variant="contained"
            onClick={() => {
              const updatedArray = fieldValue.filter((_, i) => i !== index);
              handleChange(key, updatedArray);
            }}
            sx={{
              background: COMMON_COLORS.error.main,
              color: "#ffffff",
              fontWeight: 600,
              "&:hover": {
                background: COMMON_COLORS.error.dark,
              },
            }}
          >
            Remove
          </Button>
        </div>
      ))}
      <Button
        variant="contained"
        onClick={() => handleChange(key, [...fieldValue, ""])}
        sx={{
          background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
          color: "#ffffff",
          fontWeight: 600,
          "&:hover": {
            background: "linear-gradient(135deg, #059669 0%, #047857 100%)",
          },
        }}
      >
        Add Time
      </Button>
    </div>
  );

  // Render boolean field (switch)
  const renderBooleanField = (key, fieldValue) => (
    <Switch
      id={key}
      checked={fieldValue}
      onChange={(e) => handleChange(key, e.target.checked)}
      className="ml-auto"
      sx={{
        "& .MuiSwitch-switchBase.Mui-checked": {
          color: themeColors.secondary.main,
        },
        "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
          backgroundColor: themeColors.secondary.main,
        },
      }}
    />
  );

  // Render select field
  const renderSelectField = (key, fieldValue, options) => (
    <FormControl fullWidth>
      <Select
        id={key}
        value={fieldValue || options[0]?.value || ""}
        onChange={(e) => handleChange(key, e.target.value)}
        sx={{
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.primary.main,
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.main,
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: themeColors.secondary.light,
          },
        }}
      >
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );

  // Render text field with optional password visibility toggle
  const renderTextField = (key, fieldValue, isPassword) => (
    <div className="flex flex-grow items-center gap-2">
      <TextField
        className={isPassword ? "" : "pr-12"}
        id={key}
        type={
          isPassword && passwordVisibility[key]
            ? "text"
            : isPassword
            ? "password"
            : "text"
        }
        value={fieldValue || ""}
        onChange={(e) => handleChange(key, e.target.value)}
        fullWidth
      />
      {isPassword && (
        <IconButton
          onClick={() => togglePasswordVisibility(key)}
          title={passwordVisibility[key] ? "Hide" : "Show"}
          sx={{
            color: COMMON_COLORS.text.muted,
            transition: TRANSITIONS.default,
            "&:hover": {
              color: themeColors.secondary.main,
              backgroundColor: themeColors.alpha.hover,
            },
          }}
        >
          {passwordVisibility[key] ? <VisibilityOff /> : <Visibility />}
        </IconButton>
      )}
      <IconButton
        onClick={() => navigator.clipboard.writeText(fieldValue || "")}
        title="Copy to clipboard"
        sx={{
          color: COMMON_COLORS.text.muted,
          transition: TRANSITIONS.default,
          "&:hover": {
            color: themeColors.secondary.main,
            backgroundColor: themeColors.alpha.hover,
          },
        }}
      >
        <ContentCopy />
      </IconButton>
    </div>
  );

  // Main render field function
  const renderField = (key) => {
    const fieldValue = value[key];
    const isPassword = key.toLowerCase().includes("password");
    const fieldConfig = typeConfig[key];

    // Check if field has custom type configuration
    if (fieldConfig?.type === "select" && fieldConfig?.options) {
      return renderSelectField(key, fieldValue, fieldConfig.options);
    } else if (Array.isArray(fieldValue)) {
      return renderArrayField(key, fieldValue);
    } else if (typeof fieldValue === "boolean") {
      return renderBooleanField(key, fieldValue);
    } else {
      return renderTextField(key, fieldValue, isPassword);
    }
  };

  // Render a section with grouped fields
  const renderSection = (sectionKey, sectionData, index, length) => {
    if (!sectionKey || !sectionData || !sectionData.fields?.length) return null;

    const { fields, icon } = sectionData;
    const isLastSection = index + 1 >= length;

    return (
      <div key={sectionKey} className="mb-8">
        {/* Section header */}
        <div className="mb-4 flex items-center gap-4">
          {icon && (
            <div className="text-2xl" style={{ color: themeColors.secondary.main }}>
              {icon}
            </div>
          )}
          <h2
            className="text-2xl font-semibold capitalize"
            style={{ color: COMMON_COLORS.text.secondary }}
          >
            {sectionKey.replace(/_/g, " ")}
          </h2>
        </div>

        {/* Section fields */}
        <div className="space-y-6">
          {fields.map((fieldKey) => {
            const isArrayField = Array.isArray(value[fieldKey]);

            return (
              <div
                key={fieldKey}
                className={isArrayField ? "" : "flex items-center gap-4"}
              >
                <label
                  className={`flex gap-4 text-lg font-medium capitalize ${
                    isArrayField ? "mb-4" : "w-1/4"
                  }`}
                  style={{ color: COMMON_COLORS.text.tertiary }}
                >
                  {customIcons[fieldKey] && (
                    <div
                      className="flex items-center"
                      style={{ color: themeColors.secondary.main }}
                    >
                      {customIcons[fieldKey]}
                    </div>
                  )}
                  {fieldKey.replace(/_/g, " ")}:
                </label>
                <div className={isArrayField ? "" : "flex w-3/4"}>
                  {renderField(fieldKey)}
                </div>
              </div>
            );
          })}
        </div>

        {/* Section divider */}
        {!isLastSection && (
          <Divider sx={{ borderColor: themeColors.alpha.divider, mt: 3 }} />
        )}
      </div>
    );
  };

  if (error) return <p className="text-red-500">{error}</p>;

  // Render standalone fields (no sections)
  const renderStandaloneFields = () =>
    Object.keys(value).map((key) => {
      const isArrayField = Array.isArray(value[key]);

      return (
        <div
          key={key}
          className={`mb-6 ${isArrayField ? "" : "flex items-center gap-4"}`}
        >
          <label
            className={`flex gap-4 text-lg font-medium capitalize ${
              isArrayField ? "mb-4" : "w-1/4"
            }`}
            style={{ color: COMMON_COLORS.text.tertiary }}
          >
            {customIcons[key] && (
              <div
                className="flex items-center"
                style={{ color: themeColors.secondary.main }}
              >
                {customIcons[key]}
              </div>
            )}
            {key.replace(/_/g, " ")}:
          </label>
          <div className={isArrayField ? "" : "flex w-3/4"}>
            {renderField(key)}
          </div>
        </div>
      );
    });

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="mb-10">
        {customSections
          ? Object.keys(customSections).map((sectionKey, index) =>
              renderSection(
                sectionKey,
                customSections[sectionKey],
                index,
                Object.keys(customSections).length
              )
            )
          : renderStandaloneFields()}
      </div>
      <SaveButton onSave={handleSubmit} alert={alert} setAlert={setAlert} />
    </form>
  );
}
