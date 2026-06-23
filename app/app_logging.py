import logging
from collections.abc import Callable

from .config import LOGS_DIR


StatusCallback = Callable[[str], None]
LOG_FILE = LOGS_DIR / "sync.log"

logger = logging.getLogger("tpu_calendar_sync")
logger.setLevel(logging.INFO)
logger.propagate = False

_file_logging_configured = False
_file_logging_failed = False


def configure_file_logging() -> bool:
    global _file_logging_configured
    global _file_logging_failed

    if _file_logging_configured:
        return True

    if _file_logging_failed:
        return False

    try:
        LOGS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        file_handler = logging.FileHandler(
            LOG_FILE,
            encoding="utf-8"
        )

    except OSError:
        _file_logging_failed = True
        return False

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )
    )
    logger.addHandler(file_handler)
    _file_logging_configured = True

    return True


def emit(
    message: str,
    status_callback: StatusCallback | None = None
) -> None:
    if configure_file_logging():
        logger.info(message)

    if status_callback:
        status_callback(message)
        return

    print(message)
