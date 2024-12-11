import React from "react";
import { Button, Snackbar, Alert } from "@mui/material";
import SaveIcon from "@mui/icons-material/Save";

const SaveButton = ({ onSave, alert, setAlert }) => {
  return (
    <>
      <Button
        className="mt-5 flex gap-2 bg-blue-500  text-white hover:bg-blue-900"
        variant="contained"
        color="primary"
        onClick={onSave}
      >
        <SaveIcon />
        Save
      </Button>
      <Snackbar
        open={alert.open}
        autoHideDuration={3000}
        onClose={() => setAlert({ ...alert, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity={alert.type} variant="outlined">
          {alert.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default SaveButton;
