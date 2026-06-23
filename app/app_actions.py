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
            f"Файл Google credentials.json не найден: {CREDENTIALS_FILE}"
        )

    get_calendar_service(status_callback=status_callback)

    emit(
        "Успешный вход в аккаунт Google.",
        status_callback
    )

    return True


def logout_google_account(
    status_callback: StatusCallback | None = None
) -> bool:
    if not TOKEN_FILE.exists():
        emit(
            "Вход в Google не выполнен.",
            status_callback
        )

        return False

    TOKEN_FILE.unlink()

    emit(
        "Выход из аккаунта Google выполнен.",
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
