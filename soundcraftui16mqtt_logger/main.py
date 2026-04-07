from loguru import logger
from sys import stderr
from os import path


def define_logger(
    loglevel: str = "INFO",
    to_file: bool = False,
    logfile: str = "/opt/soundcraftui16mqtt_log/default.log"
) -> None:
    allowed_levels = [
        "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
    ]

    # Remove existing Loggers
    logger.remove()

    # Add stderr logger
    logger.add(
        stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}:{function}</cyan>:<cyan>{line}</cyan> "
            "- <level>{message}</level>"
        ),
        level=loglevel if loglevel in allowed_levels else "INFO",
        colorize=True
    )
    # Send info about loglevel change if not correct level was given
    if loglevel not in allowed_levels:
        logger.warning(
            f"loglevel changed to 'INFO' because {loglevel} is unkown. "
            "Allowed levels: {allowed_levels}"
        )

    # Add logging to file if to_file set
    if to_file and not path.isdir(path.split(logfile)[0]):
        logger.error(
            f"Make sure directory {path.split(logfile)[0]} exists with access"
            " for your user"
        )
    elif to_file:
        try:
            logger.add(
                logfile,
                format=(
                    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                    "{name}:{function} | {message}"
                ),
                level=loglevel if loglevel in allowed_levels else "INFO",
                colorize=False
            )
        except PermissionError:
            logger.error(
                f"Could not create logging to file {logfile}."
                " Make sure your user can access the directory and file"
            )
    logger.debug("Logger setup complete!")
