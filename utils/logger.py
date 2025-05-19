"""
Centralized logging utility
"""
import logging
import logging.config
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

# Configuration de base par défaut - sera remplacée plus tard
DEFAULT_LOGS_DIR = Path("logs")
DEFAULT_LOGS_DIR.mkdir(exist_ok=True)

# Configure logging with basic settings initially
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class Logger:
    """
    Enhanced logger wrapper for standardized logging across the application
    """

    def __init__(self, name: str):
        """
        Initialize logger for the specified module

        Args:
            name: Module name (usually __name__)
        """
        self.logger = logging.getLogger(name)
        self.module = name

    def debug(self, message: str, **kwargs) -> None:
        """
        Log a debug message

        Args:
            message: Message to log
            **kwargs: Additional contextual data
        """
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """
        Log an info message

        Args:
            message: Message to log
            **kwargs: Additional contextual data
        """
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """
        Log a warning message

        Args:
            message: Message to log
            **kwargs: Additional contextual data
        """
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """
        Log an error message

        Args:
            message: Message to log
            **kwargs: Additional contextual data
        """
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """
        Log a critical message

        Args:
            message: Message to log
            **kwargs: Additional contextual data
        """
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def exception(self, message: str, exc: Optional[Exception] = None, **kwargs) -> None:
        """
        Log an exception with traceback

        Args:
            message: Message to log
            exc: Exception to log (optional)
            **kwargs: Additional contextual data
        """
        if exc:
            kwargs['exception'] = f"{type(exc).__name__}: {str(exc)}"
        self.logger.exception(message, extra=self._format_kwargs(**kwargs))

    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """
        Internal logging method

        Args:
            level: Log level
            message: Message to log
            **kwargs: Additional contextual data
        """
        self.logger.log(level.value, message, extra=self._format_kwargs(**kwargs))

    def _format_kwargs(self, **kwargs) -> dict:
        """
        Format additional data for logging

        Args:
            **kwargs: Additional contextual data

        Returns:
            Formatted data dictionary
        """
        # Add standard fields
        result = {
            'app_module': self.module,
            'timestamp': datetime.now().isoformat()
        }

        # Add custom fields
        if kwargs:
            result['context'] = kwargs

        return result


def get_logger(name: str) -> Logger:
    """
    Get a configured logger for the specified module

    Args:
        name: Module name (usually __name__)

    Returns:
        Configured logger
    """
    return Logger(name)


def log_exception(logger: Logger, e: Exception, message: Optional[str] = None) -> None:
    """
    Log an exception with an optional message

    Args:
        logger: Logger to use
        e: Exception to log
        message: Optional message to include
    """
    if message:
        logger.exception(f"{message}: {str(e)}", exc=e)
    else:
        logger.exception(str(e), exc=e)


def configure_logging(config: Dict[str, Any], logs_dir: Path) -> None:
    """
    Configure logging with the provided configuration

    Args:
        config: Logging configuration dictionary
        logs_dir: Directory for log files
    """
    # Ensure the logs directory exists
    logs_dir.mkdir(exist_ok=True)

    # Apply configuration
    logging.config.dictConfig(config)


def setup_file_logging(user_id: Optional[str] = None) -> Path:
    """
    Configure logging to a file specific to the user

    Args:
        user_id: User ID (if applicable)

    Returns:
        Path to the log file
    """
    # Get logs directory (use global if configured, otherwise default)
    logs_dir = DEFAULT_LOGS_DIR

    # Create log file name
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id:
        log_file = logs_dir / f"user_{user_id}_{today}.log"
    else:
        log_file = logs_dir / f"app_{today}.log"

    # Configure a file handler
    file_handler = logging.FileHandler(str(log_file))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    # Add handler to root logger
    logging.getLogger('').addHandler(file_handler)

    return log_file