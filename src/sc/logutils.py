import logging

COLOURS = {
    'DEBUG':    '\x1b[90m',   # Grey
    'INFO':     '\x1b[32m',   # Green
    'WARNING':  '\x1b[33m',   # Yellow
    'ERROR':    '\x1b[31m',   # Red
}
RESET = '\x1b[0m'

DEFAULT_FMT = '[%(levelname)s] [%(plugin)s] %(message)s'
DEBUG_FMT = '[%(levelname)s] [%(plugin)s] %(name)s: %(message)s'

class ScLoggerFormatter(logging.Formatter):
    """Custom formatter that injects a plugin name into each log record."""
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        super().__init__()

    def format(self, record):
        record.plugin = self.plugin_name
        colour = COLOURS.get(record.levelname, RESET)
        record.levelname = f"{colour}{record.levelname}{RESET}"

        if ScLoggerManager.get_level() == logging.DEBUG:
            self._style._fmt = DEBUG_FMT
        else:
            self._style._fmt = DEFAULT_FMT
        return super().format(record)

class ScLoggerManager:
    """Manages logger configuration for a plugin.
    
    Initialize with a plugin name, then call `add_loggers` with logger names to configure.
    Each log message will include the plugin name and be output to stdout.

    Usage:
        manager = ScLoggerManager("my_plugin")
        manager.add_loggers(["my_plugin", "tracked_logger"])
    """
    _level = logging.INFO

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name

    @classmethod
    def set_level(cls, level: int):
        cls._level = level
    
    @classmethod
    def get_level(cls):
        return cls._level

    def add_loggers(self, logger_names: list[str]):
        handler = self._create_handler()
        for name in logger_names:
            logger = logging.getLogger(name)
            logger.setLevel(self._level)
            logger.addHandler(handler)
            logger.propagate = False

    def _create_handler(self) -> logging.Handler:
        handler = logging.StreamHandler()
        formatter = ScLoggerFormatter(plugin_name=self.plugin_name)
        handler.setFormatter(formatter)
        return handler
