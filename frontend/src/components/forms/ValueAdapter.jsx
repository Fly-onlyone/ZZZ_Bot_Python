import React from "react";
import { Box, Button, Divider, Snackbar, Stack, Alert } from "@mui/material";
import { motion } from "framer-motion";
import SaveStatus from "../common/SaveStatus";
import { COMMON_COLORS } from "../../theme/colors";
import { useThemeContext } from "../../theme/ThemeContext";
import { useFieldRenderer, useFormState } from "../../hooks";

/**
 * ValueAdapter Component
 *
 * Dynamic form generator that automatically renders appropriate input fields
 * based on data types and configuration. Edits auto-save through useFormState
 * — discrete controls commit on change, text inputs commit on blur. A
 * SaveStatus pill at the top of the rendered output surfaces save state.
 *
 * @param {Object} customIcons - Icon mappings for specific fields
 * @param {Object} customSections - Section configuration with fields and icons
 * @param {Object} typeConfig - Custom type configuration (e.g., select options)
 * @param {Array} extraActions - Additional action buttons displayed below the form
 */
export default function ValueAdapter({
  customIcons = {},
  customSections = null,
  typeConfig = {},
  extraActions = [],
  route,
}) {
  const { themeColors } = useThemeContext();
  const { value, error, handleChange, commit, autoSave } = useFormState(route);
  const { renderField } = useFieldRenderer(typeConfig);
  const [actionLoading, setActionLoading] = React.useState({});
  const [actionAlert, setActionAlert] = React.useState({
    open: false,
    type: "success",
    message: "",
  });
  /** @type {{key: string, label: string, onClick: Function, successMessage?: string | Function, errorMessage?: string}[]} */
  const actions = Array.isArray(extraActions) ? extraActions : [];
  const resolvedSections =
    typeof customSections === "function" ? customSections(value) : customSections;

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
      <div key={fieldKey} className={isArrayField ? "" : "flex items-center gap-4"}>
        <label
          className={`flex gap-4 text-lg font-medium capitalize ${isArrayField ? "mb-4" : "w-1/4"}`}
          style={{ color: COMMON_COLORS.text.secondary }}
        >
          {customIcons[fieldKey] && (
            <div className="flex items-center" style={{ color: themeColors.secondary.main }}>
              {customIcons[fieldKey]}
            </div>
          )}
          {typeConfig[fieldKey]?.label || fieldKey.replace(/_/g, " ")}:
        </label>
        <div className={isArrayField ? "" : isThemeField ? "flex w-3/4 justify-end" : "flex w-3/4"}>
          {renderField(
            fieldKey,
            value[fieldKey],
            (newValue) => handleChange(fieldKey, newValue),
            commit,
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
              style={{
                color: themeColors.secondary.main,
                filter: `drop-shadow(0 0 6px ${themeColors.glow}40)`,
              }}
            >
              {icon}
            </div>
          )}
          <h2
            className="text-2xl font-semibold capitalize"
            style={{
              color: COMMON_COLORS.text.secondary,
              textShadow: `0 0 15px ${themeColors.glow}25`,
            }}
          >
            {sectionKey.replace(/_/g, " ")}
          </h2>
        </div>

        {/* Section fields */}
        <div className="space-y-6">{fields.map((fieldKey) => renderFieldRow(fieldKey))}</div>

        {/* Section divider */}
        {!isLastSection && <Divider sx={{ borderColor: themeColors.alpha.divider, mt: 3 }} />}
      </div>
    );
  };

  /**
   * Renders standalone fields (no sections)
   */
  const renderStandaloneFields = () => (
    <div className="space-y-6">{Object.keys(value).map((key) => renderFieldRow(key))}</div>
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
      setActionAlert({
        open: true,
        type: "success",
        message: successMessage,
      });
    } catch (error) {
      const fallbackMessage = error instanceof Error ? error.message : "Action failed.";
      setActionAlert({
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
      onClick={() => {
        void handleExtraAction(action);
      }}
      disabled={Boolean(actionLoading[action.key])}
      sx={{
        borderColor: `${COMMON_COLORS.warning.main}80`,
        color: COMMON_COLORS.warning.light,
        backdropFilter: "blur(8px)",
        "&:hover": {
          borderColor: COMMON_COLORS.warning.main,
          background: `${COMMON_COLORS.warning.main}15`,
          boxShadow: `0 0 25px ${COMMON_COLORS.warning.main}30`,
        },
      }}
    >
      {actionLoading[action.key] ? "Running..." : action.label}
    </Button>
  ));

  const handleCloseActionAlert = () => {
    setActionAlert((prev) => ({ ...prev, open: false }));
  };

  return (
    <div className="space-y-6">
      <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1, minHeight: 28 }}>
        <SaveStatus status={autoSave.status} error={autoSave.error} onRetry={autoSave.retry} />
      </Box>
      <div className="mb-10">
        {resolvedSections
          ? Object.keys(resolvedSections).map((sectionKey, index) =>
              renderSection(
                sectionKey,
                resolvedSections[sectionKey],
                index,
                Object.keys(resolvedSections).length,
              ),
            )
          : renderStandaloneFields()}
      </div>
      {actions.length > 0 && (
        <Stack direction="row" spacing={2}>
          {actionButtons}
        </Stack>
      )}
      <Snackbar
        open={actionAlert.open}
        autoHideDuration={3000}
        onClose={handleCloseActionAlert}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          transition={{ duration: 0.3 }}
        >
          <Alert severity={actionAlert.type} variant="outlined">
            {actionAlert.message}
          </Alert>
        </motion.div>
      </Snackbar>
    </div>
  );
}
