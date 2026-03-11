import logging
from typing import Any

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Defines the following log levels:
#
# - `logging.NOTSET`   :  0
# - `logging.TRACE`    :  5
# - `logging.DEBUG`    : 10
# - `logging.INFO`     : 20
# - `logging.WARNING`  : 30
# - `logging.NOTICE`   : 25
# - `logging.SUCCESS`  : 40

logging.NOTICE = 25
logging.addLevelName(logging.NOTICE, "NOTICE")
logging.SUCCESS = 40
logging.addLevelName(logging.SUCCESS, "SUCCESS")
FORMAT = "[%(name)-16s] %(message)s"


class TLULogger(logging.Logger):
    """Custom Logger class for Constellation."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Init logger."""
        super().__init__(*args, **kwargs)

    def success(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Define level for verbose information which allows to follow the call
        stack of the host program."""
        self.log(logging.SUCCESS, msg, *args, **kwargs)  # type: ignore[attr-defined]

    def notice(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Define level for important information about the host program to the
        end user with low frequency."""
        self.log(logging.NOTICE, msg, *args, **kwargs)  # type: ignore[attr-defined]


def setup_main_logger(name="AidaTLU", level="INFO"):
    """Sets up the CLI logging configuration"""
    # Get log level integer
    level_number = logging.getLevelNamesMapping()[level.upper()]
    console_theme = Theme(
        {
            "logging.level.debug": "magenta",
            "logging.level.info": "",
            "logging.level.warning": "bold yellow",
            "logging.level.success": "bold green",
            "logging.level.notice": "blue",
            "logging.level.error": "bold red",
            "logging.level.critical": "bold red",
        }
    )
    handler = RichHandler(
        level=level_number,
        console=Console(theme=console_theme),
        show_path=False,
        show_time=True,
        omit_repeated_times=False,
        log_time_format="|%Y-%m-%d %H:%M:%S|",
    )
    # Logging configuration
    logging.basicConfig(level=level, format=FORMAT, handlers=[handler])
    # Set TLULogger as default logging class
    logging.setLoggerClass(TLULogger)
    logger = logging.getLogger(name)

    return logger


def setup_derived_logger(name):
    logging.setLoggerClass(TLULogger)
    logger = logging.getLogger(name)

    return logger
