import logging


class StreamToLogger(object):
    """Redirect writes to a logger without splitting partial lines."""

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self._buffer = ""

    def write(self, buf):
        text = str(buf)
        if not text:
            return 0

        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")
            if line:
                self.logger.log(self.level, line)

        return len(text)

    def flush(self):
        if not self._buffer:
            return

        line = self._buffer.rstrip("\r")
        self._buffer = ""
        if line:
            self.logger.log(self.level, line)


class NoImportFilter(logging.Filter):
    def filter(self, record):
        # return False to drop any message containing "Importing"
        return "Importing" not in record.getMessage()
