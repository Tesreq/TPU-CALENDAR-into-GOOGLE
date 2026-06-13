import logging
from collections.abc import Callable

from config import LOGS_DIR


StatusCallback = Callable[[str], None]

LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "sync.log"

logger = logging.getLogger("tpu_calendar_sync")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )
    )

    logger.addHandler(file_handler)


def emit(
    message: str,
    status_callback: StatusCallback | None = None
) -> None:
    logger.info(message)

    if status_callback:
        status_callback(message)
        return

    print(message)
