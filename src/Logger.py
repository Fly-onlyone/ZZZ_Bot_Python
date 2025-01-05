import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler


class Logger:
    """Redirects `print` statements and uncaught exceptions to a log file."""

    def __init__(self, log_file, retention_days=30):
        self.log_file = log_file
        self.retention_days = retention_days
        self._configure_logging()
        self._schedule_log_cleanup()

    def _configure_logging(self):
        """Configure logging using `TimedRotatingFileHandler`."""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Timed rotating file handler
        file_handler = TimedRotatingFileHandler(
            self.log_file,
            when="W0",  # Rotate at midnight
            interval=1,  # Rotate daily
            backupCount=0,  # No built-in deletion; we'll handle it
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(file_handler)

        # Add a safe console handler
        try:
            console_handler = logging.StreamHandler(sys.stdout or open(os.devnull, "w"))
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            logger.addHandler(console_handler)
        except Exception as e:
            logger.error(f"Failed to configure console logging: {e}")

    def _schedule_log_cleanup(self):
        """Schedule log cleanup for files older than `retention_days`."""
        log_dir = os.path.dirname(self.log_file)
        log_prefix = os.path.basename(self.log_file)

        def cleanup_logs():
            now = datetime.now()
            for filename in os.listdir(log_dir):
                if filename.startswith(log_prefix):
                    filepath = os.path.join(log_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if now - file_time > timedelta(days=self.retention_days):
                        try:
                            os.remove(filepath)
                            logging.info(f"Deleted old log file: {filepath}")
                        except Exception as e:
                            logging.error(f"Error deleting log file {filepath}: {e}")

        cleanup_logs()

    def write(self, message):
        """Redirect `print` calls to the logging system."""
        message = message.strip()  # Avoid empty log lines
        if message:
            logging.info(message)

    def flush(self):
        """Flush method for compatibility with `sys.stdout` and `sys.stderr`."""
        pass
