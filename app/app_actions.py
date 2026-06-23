import json
import shutil
from pathlib import Path

from .app_logging import StatusCallback, emit
from .calendar_api import get_calendar_service
from .config import CREDENTIALS_FILE, TOKEN_FILE
from .delete_tpu_calendar import delete_calendar
from .manage_subjects import load_subjects, save_subjects
from .sync_calendar import sync_calendar
from .sync_to_json import update_schedule


def import_google_credentials(
    source_path: str,
    status_callback: StatusCallback | None = None
) -> dict:
    source = Path(source_path).expanduser()

    if not source.exists():
        raise FileNotFoundError(
            f"Файл не найден: {source}"
        )

    try:
        with open(
            source,
            "r",
            encoding="utf-8"
        ) as file:
            credentials = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            "Выбранный файл не является корректным JSON."
        ) from error

    client = credentials.get("installed") or credentials.get("web")
    required_fields = (
        "client_id",
        "client_secret",
        "auth_uri",
        "token_uri"
    )

    if not isinstance(client, dict) or any(
        field not in client
        for field in required_fields
    ):
        raise ValueError(
            "Выбранный файл не похож на Google credentials.json."
        )

    CREDENTIALS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    same_file = (
        CREDENTIALS_FILE.exists()
        and source.resolve() == CREDENTIALS_FILE.resolve()
    )
    changed = True

    if CREDENTIALS_FILE.exists():
        changed = (
            source.read_bytes() != CREDENTIALS_FILE.read_bytes()
            if not same_file
            else False
        )

    if not same_file:
        shutil.copyfile(
            source,
            CREDENTIALS_FILE
        )

    token_removed = False

    if changed and TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        token_removed = True

    emit(
        f"Google credentials.json сохранён: {CREDENTIALS_FILE}",
        status_callback
    )

    if token_removed:
        emit(
            "Старый Google token.json удалён. Выполните вход заново.",
            status_callback
        )

    return {
        "credentials_imported": True,
        "credentials_path": str(CREDENTIALS_FILE),
        "token_removed": token_removed
    }


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
