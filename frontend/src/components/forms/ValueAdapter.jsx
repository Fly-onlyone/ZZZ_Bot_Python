import React from "react";
import { Button, Divider, Stack } from "@mui/material";
import SaveButton from "../common/SaveButton";
import { COMMON_COLORS } from "../../theme/colors";
import { useThemeContext } from "../../theme/ThemeContext";
import { useFieldRenderer, useFormState } from "../../hooks";

/**
 * ValueAdapter Component
 *
 * Dynamic form generator that automatically renders appropriate input fields
 * based on data types and configuration. Supports sections, custom icons,
 * and type-specific rendering.
 *
 * @param {Object} customIcons - Icon mappings for specific fields
 * @param {Object} customSections - Section configuration with fields and icons
 * @param {Object} typeConfig - Custom type configuration (e.g., select options)
 * @param {Array} extraActions - Additional action buttons displayed above Save
 */
export default function ValueAdapter({
  customIcons = {},
  customSections = null,
  typeConfig = {},
  extraActions = [],
  route,
}) {
  const { themeColors } = useThemeContext();
  const { value, error, handleChange, handleSubmit, alert, setAlert } =
    useFormState(route);
  const { renderField } = useFieldRenderer(typeConfig);
  const [actionLoading, setActionLoading] = React.useState({});
  /** @type {{key: string, label: string, onClick: Function, successMessage?: string | Function, errorMessage?: string}[]} */
  const actions = Array.isArray(extraActions) ? extraActions : [];
  const resolvedSections =
    typeof customSections === "function"
      ? customSections(value)
      : customSections;

  if (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return <p className="text-red-500">{errorMessage}</p>;
  }

  /**
   * Renders a single field with label and appropriate input component
   */
  const renderFieldRow = (fieldKey) => {
    const isArrayField = Array.isArray(value[fieldKey]);
    const isThemeField = fieldKey === "theme";

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
          {typeConfig[fieldKey]?.label || fieldKey.replace(/_/g, " ")}:
        </label>
        <div
          className={
            isArrayField
              ? ""
              : isThemeField
              ? "flex w-3/4 justify-end"
              : "flex w-3/4"
          }
        >
          {renderField(fieldKey, value[fieldKey], (newValue) =>
            handleChange(fieldKey, newValue)
          )}
        </div>
      </div>
    );
  };

  /**
   * Renders a section with grouped fields
   */
  const renderSection = (sectionKey, sectionData, index, length) => {
    if (!sectionKey || !sectionData || !sectionData.fields?.length) return null;

    const { fields, icon } = sectionData;
    const isLastSection = index + 1 >= length;

    return (
      <div key={sectionKey} className="mb-8">
        {/* Section header */}
        <div className="mb-4 flex items-center gap-4">
          {icon && (
            <div
              className="text-2xl"
              style={{ color: themeColors.secondary.main }}
            >
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
          {fields.map((fieldKey) => renderFieldRow(fieldKey))}
        </div>

        {/* Section divider */}
        {!isLastSection && (
          <Divider sx={{ borderColor: themeColors.alpha.divider, mt: 3 }} />
        )}
      </div>
    );
  };

  /**
   * Renders standalone fields (no sections)
   */
  const renderStandaloneFields = () => (
    <div className="space-y-6">
      {Object.keys(value).map((key) => renderFieldRow(key))}
    </div>
  );

  const handleExtraAction = async (action) => {
    if (typeof action?.onClick !== "function") {
      return;
    }

    setActionLoading((prev) => ({ ...prev, [action.key]: true }));
    try {
      const result = await action.onClick();
      const successMessage =
        typeof action.successMessage === "function"
          ? action.successMessage(result)
          : action.successMessage || "Action completed successfully!";
      setAlert({
        open: true,
        type: "success",
        message: successMessage,
      });
    } catch (error) {
      const fallbackMessage =
        error instanceof Error ? error.message : "Action failed.";
      setAlert({
        open: true,
        type: "error",
        message: action.errorMessage || fallbackMessage,
      });
    } finally {
      setActionLoading((prev) => ({ ...prev, [action.key]: false }));
    }
  };

  /** @type {React.ReactNode[]} */
  const actionButtons = actions.map((action) => (
    <Button
      key={action.key}
      variant="outlined"
      color="warning"
      onClick={() => {
        void handleExtraAction(action);
      }}
      disabled={Boolean(actionLoading[action.key])}
    >
      {actionLoading[action.key] ? "Running..." : action.label}
    </Button>
  ));

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="mb-10">
        {resolvedSections
          ? Object.keys(resolvedSections).map((sectionKey, index) =>
              renderSection(
                sectionKey,
                resolvedSections[sectionKey],
                index,
                Object.keys(resolvedSections).length
              )
            )
          : renderStandaloneFields()}
      </div>
      {actions.length > 0 && (
        <Stack direction="row" spacing={2}>
          {actionButtons}
        </Stack>
      )}
      <SaveButton onSave={handleSubmit} alert={alert} setAlert={setAlert} />
    </form>
  );
}
