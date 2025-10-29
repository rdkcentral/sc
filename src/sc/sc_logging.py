import logging

from rich.logging import RichHandler 

APP_LOGGER_NAME = "sc"

def setup_logging(debug_mode: bool = False):
    """Setup the logging for a logger."""
    plugin_logger = logging.getLogger('sc')
    if debug_mode:
        plugin_logger.setLevel(logging.DEBUG)
    else:
        plugin_logger.setLevel(logging.INFO)

    formatter = ScLoggerFormatter()
    handler = RichHandler(show_time=False, show_path=False)
    handler.setFormatter(formatter)
    plugin_logger.addHandler(handler)

def enable_library_logging(library_name: str):
    app_logger = logging.getLogger(APP_LOGGER_NAME)
    if not app_logger.handlers:
        raise RuntimeError("App logger not initialized. Call setup_logging() first.")

    lib_logger = logging.getLogger(library_name)
    lib_logger.setLevel(app_logger.level)
    lib_logger.addHandler(app_logger.handlers[0])

class ScLoggerFormatter(logging.Formatter):
    """Custom formatter that injects a plugin name into each log record."""
    DEFAULT_FMT = '[sc] %(message)s'
    DEBUG_FMT = '[sc] %(name)s: %(message)s'

    def format(self, record):
        if record.levelno == logging.DEBUG:
            self._style._fmt = self.DEBUG_FMT
        else:
            self._style._fmt = self.DEFAULT_FMT
        return super().format(record)
    