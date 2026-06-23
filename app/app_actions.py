from .app_logging import StatusCallback, emit
from .calendar_api import get_calendar_service
from .config import CREDENTIALS_FILE, TOKEN_FILE
from .delete_tpu_calendar import delete_calendar
from .manage_subjects import load_subjects, save_subjects
from .sync_calendar import sync_calendar
from .sync_to_json import update_schedule


def login_google_account(
    status_callback: StatusCallback | None = None
) -> bool:
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Google credentials file not found: {CREDENTIALS_FILE}"
        )

    get_calendar_service(status_callback=status_callback)

    emit(
        "Google account has been connected.",
        status_callback
    )

    return True


def logout_google_account(
    status_callback: StatusCallback | None = None
) -> bool:
    if not TOKEN_FILE.exists():
        emit(
            "Google account is not connected.",
            status_callback
        )

        return False

    TOKEN_FILE.unlink()

    emit(
        "Google account has been disconnected.",
        status_callback
    )

    return True


def full_sync(
    status_callback: StatusCallback | None = None
) -> dict:
    schedule_result = update_schedule(status_callback=status_callback)
    calendar_result = sync_calendar(status_callback=status_callback)

    return {
        "schedule": schedule_result,
        "calendar": calendar_result
    }
