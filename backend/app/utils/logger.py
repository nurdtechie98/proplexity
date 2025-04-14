import logging
import sys
from typing import Optional


class ServiceLogger:
    """Centralized logging utility for services."""

    _logger: Optional[logging.Logger] = None

    @classmethod
    def setup(cls, log_level: int = logging.INFO) -> None:
        """Set up the logger with proper formatting."""
        if not cls._logger:
            logger = logging.getLogger("wayback")
            logger.setLevel(log_level)

            # Console handler
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(log_level)

            # Format with timestamp, service name, and message
            formatter = logging.Formatter(
                "%(asctime)s [%(service)s] %(levelname)s: %(message)s"
            )
            handler.setFormatter(formatter)

            logger.addHandler(handler)
            cls._logger = logger

    @classmethod
    def _get_logger(cls) -> logging.Logger:
        """Get or create the logger."""
        if not cls._logger:
            cls.setup()
        return cls._logger

    @classmethod
    def info(cls, service: str, message: str) -> None:
        """Log an info message."""
        cls._get_logger().info(message, extra={"service": service})

    @classmethod
    def error(cls, service: str, message: str) -> None:
        """Log an error message."""
        cls._get_logger().error(message, extra={"service": service})

    @classmethod
    def debug(cls, service: str, message: str) -> None:
        """Log a debug message."""
        cls._get_logger().debug(message, extra={"service": service})

    @classmethod
    def warning(cls, service: str, message: str) -> None:
        """Log a warning message."""
        cls._get_logger().warning(message, extra={"service": service})
