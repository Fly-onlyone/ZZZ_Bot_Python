import React from "react";
import { Divider } from "@mui/material";
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
 */
export default function ValueAdapter({
  customIcons = {},
  customSections = null,
  typeConfig = {},
}) {
  const { themeColors } = useThemeContext();
  const { value, error, handleChange, handleSubmit, alert, setAlert } =
    useFormState();
  const { renderField } = useFieldRenderer(typeConfig);

  if (error) return <p className="text-red-500">{error}</p>;

  /**
   * Renders a single field with label and appropriate input component
   */
  const renderFieldRow = (fieldKey) => {
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
