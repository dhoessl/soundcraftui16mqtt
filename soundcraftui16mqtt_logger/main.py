from loguru import logger
from sys import stderr


def define_logger(debug: bool = False, to_file: bool = False) -> None:
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}:{function}</cyan>:<cyan>{line}</cyan> "
        "- <level>{message}</level>"
    )
    logger.remove()
    logger.add(
        stderr,
        format=log_format,
        level="INFO" if not debug else "DEBUG",
        colorize=True
    )
    if to_file:
        logger.add(
            "/opt/soundcraftui16mqtt_log/default.log",
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function} | {message}"
            ),
            level="DEBUG",
            colorize=False
        )
    logger.debug("Logger setup complete!")
