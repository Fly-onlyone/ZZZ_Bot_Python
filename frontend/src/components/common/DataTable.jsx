import React, { memo } from "react";
import { Box } from "@mui/material";
import { motion } from "framer-motion";
import { useThemeContext } from "../../theme/ThemeContext";
import { COMMON_COLORS } from "../../theme/colors";

/**
 * Animation variants for table rows
 */
const tableRowVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (index) => ({
    opacity: 1,
    x: 0,
    transition: {
      delay: index * 0.05,
      type: "spring",
      stiffness: 100,
      damping: 15,
    },
  }),
};

/**
 * Reusable DataTable component with theme-aware styling
 *
 * @param {object} props
 * @param {Array<{key: string, label: string, width?: string}>} props.columns - Column definitions
 * @param {Array<object>} props.data - Row data
 * @param {function} props.renderCell - Function to render cell content (row, columnKey, rowIndex) => ReactNode
 * @param {function} [props.getRowBackground] - Optional function to get row background (row, index) => string
 * @param {function} [props.getRowHoverBackground] - Optional function to get row hover background (row, index) => string
 */
const DataTable = memo(function DataTable({
  columns,
  data,
  renderCell,
  getRowBackground,
  getRowHoverBackground,
}) {
  const { themeColors } = useThemeContext();

  const defaultRowBg = themeColors.alpha.card;
  const defaultHoverBg = themeColors.alpha.hover;

  return (
    <Box
      sx={{
        borderRadius: "12px",
        overflow: "hidden",
        border: `1px solid ${themeColors.alpha.divider}`,
      }}
    >
      <Box
        component="table"
        sx={{
          width: "100%",
          borderCollapse: "collapse",
        }}
        role="table"
      >
        <Box
          component="thead"
          sx={{
            background: themeColors.gradients.header,
          }}
        >
          <Box component="tr" role="row">
            {columns.map((col) => (
              <Box
                key={col.key}
                component="th"
                role="columnheader"
                sx={{
                  px: 3,
                  py: 2,
                  textAlign: "left",
                  fontWeight: 600,
                  color: COMMON_COLORS.text.secondary,
                  borderBottom: `1px solid ${themeColors.alpha.divider}`,
                  width: col.width,
                }}
              >
                {col.label}
              </Box>
            ))}
          </Box>
        </Box>
        <Box component="tbody">
          {data.map((row, index) => (
            <Box
              component={motion.tr}
              key={row.id ?? index}
              custom={index}
              variants={tableRowVariants}
              initial="hidden"
              animate="visible"
              role="row"
              sx={{
                background: getRowBackground
                  ? getRowBackground(row, index)
                  : defaultRowBg,
                transition: "all 0.2s ease-in-out",
                "&:hover": {
                  background: getRowHoverBackground
                    ? getRowHoverBackground(row, index)
                    : defaultHoverBg,
                },
                borderBottom:
                  index !== data.length - 1
                    ? `1px solid ${themeColors.alpha.card}`
                    : "none",
              }}
            >
              {columns.map((col) => (
                <Box
                  key={col.key}
                  component="td"
                  role="cell"
                  sx={{
                    px: 3,
                    py: 2,
                  }}
                >
                  {renderCell(row, col.key, index)}
                </Box>
              ))}
            </Box>
          ))}
        </Box>
      </Box>
    </Box>
  );
});

export default DataTable;
