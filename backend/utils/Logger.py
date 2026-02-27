import logging


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


class NoImportFilter(logging.Filter):
    def filter(self, record):
        # return False to drop any message containing "Importing"
        return "Importing" not in record.getMessage()
