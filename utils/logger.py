import sys
from loguru import logger

# Configure the logger to use a standard format
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# You can also configure a file logger if needed
# logger.add("file.log", rotation="500 MB")

__all__ = ["logger"]