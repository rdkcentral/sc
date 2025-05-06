import logging

from rich.logging import RichHandler

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR

LEVELS = {
    'DEBUG': DEBUG,
    'INFO': INFO,
    'WARNING': WARNING,
    'ERROR': ERROR
}

DEFAULT_FMT = '[%(plugin)s] %(message)s'
DEBUG_FMT = '[%(plugin)s] %(name)s: %(message)s'

class ScLoggerFormatter(logging.Formatter):
    """Custom formatter that injects a plugin name into each log record."""
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        super().__init__()

    def format(self, record):
        record.plugin = self.plugin_name
        if ScLoggerManager.get_level() == DEBUG:
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
    _level = INFO

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name

    @classmethod
    def set_level(cls, level: int):
        cls._level = level
    
    @classmethod
    def get_level(cls):
        return cls._level

    def add_loggers(self, logger_names: list[str]):
        """Register one or more logger names to be managed for your plugin.
        
        Logger names should match those used in `logging.getLogger(name)`
        This is typically the module's `__name__` which resolves to the full import
        path (e.g. 'my_package.my_module') when the module is imported.

        You can register just the top level package name (e.g. 'my_package) to
        manage all loggers under that namespace, as child loggers inherit settings
        unless overridden.
        """
        if (
            not isinstance(logger_names, str) or 
            not all(isinstance(name, str) for name in logger_names)
        ):
            raise TypeError("logger_names must be list of strings!")

        handler = self._create_handler()
        for name in logger_names:
            logger = logging.getLogger(name)
            logger.setLevel(self._level)
            logger.addHandler(handler)
            logger.propagate = False

    def _create_handler(self) -> logging.Handler:
        handler = RichHandler(show_time=False, show_path=False)
        formatter = ScLoggerFormatter(plugin_name=self.plugin_name)
        handler.setFormatter(formatter)
        return handler
