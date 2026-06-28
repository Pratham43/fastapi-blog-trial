import sys
from pathlib import Path

from loguru import logger


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=False,
    enqueue=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:"
        "<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
)

logger.add(
    LOG_DIR / "app.log",
    level="INFO",
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    enqueue=True,
    backtrace=True,
    diagnose=False,
    format=(
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level} | "
        "{name}:{function}:{line} | "
        "{message}"
    ),
)