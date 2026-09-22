"""Enterprise logging subsystem configured via Loguru.

Provides structured, thread-safe, and asynchronous logging across all pipeline modules.
"""

import sys
from loguru import logger
from src.config import settings


def setup_logging() -> None:
    """Configures Loguru logger sinks, formatting, and severity levels."""
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL.upper(),
        colorize=True,
        enqueue=True,
    )

    # Optional file sink for persistent operational auditing
    logger.add(
        "logs/pipeline_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="50 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
    )


# Initialize default logging handler upon import
setup_logging()

__all__ = ["logger", "setup_logging"]
