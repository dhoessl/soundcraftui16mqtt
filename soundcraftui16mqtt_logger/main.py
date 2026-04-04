from loguru import logger
from sys import stderr


def define_logger(debug: bool = False) -> None:
    log_level = "INFO" if not debug else "DEBUG"
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}:{function}</cyan>:<cyan>{line}</cyan> "
        "- <level>{message}</level>"
    )
    logger.remove()
    logger.add(stderr, format=log_format, level=log_level, colorize=True)
    logger.debug("Logger setup complete!")
