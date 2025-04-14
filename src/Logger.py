import logging
import os
import sys
import tkinter as tk
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from tkinter import messagebox


class Logger:
    def __init__(self, log_file, retention_days=7, auto_restart=True):
        self.log_file = log_file
        self.retention_days = retention_days
        self.auto_restart = auto_restart
        self._configure_logging()
        self._schedule_log_cleanup()
        sys.excepthook = self._handle_exception  # Capture uncaught exceptions

        # Redirect print output to our custom write() method
        sys.stdout = self
        sys.stderr = self

    def _configure_logging(self):
        """Set up file and console logging."""
        self.logger = logging.getLogger("SafeLogger")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")

        # File handler with rotation
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB per file
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler using the original stdout (sys.__stdout__)
        console_handler = logging.StreamHandler(sys.__stdout__)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _schedule_log_cleanup(self):
        """Delete logs older than retention_days."""
        log_dir = os.path.dirname(self.log_file) or "."
        now = datetime.now()

        for filename in os.listdir(log_dir):
            if filename.startswith(os.path.basename(self.log_file)):
                filepath = os.path.join(log_dir, filename)
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    if (now - file_time).days > self.retention_days:
                        os.remove(filepath)
                        self.logger.info(f"Deleted old log file: {filepath}")
                except Exception as e:
                    self.logger.error(f"Error deleting log file {filepath}: {e}")

    def write(self, message):
        message = message.strip()
        if not message:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"{timestamp}: {message}\n"
        for handler in self.logger.handlers:
            try:
                handler.acquire()
                if handler.stream and hasattr(handler.stream, "write"):
                    handler.stream.write(formatted_message)
                    handler.flush()
            except Exception as e:
                # Optionally write the error to the original stderr
                sys.__stderr__.write(f"Logger.write() error: {e}\n")
                sys.__stderr__.flush()
            finally:
                handler.release()

    def flush(self):
        """Flush method for compatibility with sys.stdout and sys.stderr."""
        for handler in self.logger.handlers:
            if hasattr(handler, "flush"):
                handler.flush()

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions: log, show popup, and optionally auto-restart."""
        error_msg = "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
        self.logger.critical(f"Unhandled Exception:\n{error_msg}")

        # Show Tkinter popup
        try:
            self._show_popup(error_msg)
        except Exception as e:
            self.logger.error(f"Error showing popup: {e}")

        if self.auto_restart:
            self.logger.info("Attempting auto-restart...")
            python = sys.executable
            os.execl(python, python, *sys.argv)

    def _show_popup(self, message):
        """Display a Tkinter popup with the fatal error message."""
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Fatal Error", f"An error occurred:\n{message}")
        root.destroy()
