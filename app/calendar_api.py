from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .app_logging import StatusCallback, emit
from .config import CREDENTIALS_FILE, TOKEN_FILE


SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


def load_saved_credentials(
    status_callback: StatusCallback | None = None,
    emit_errors: bool = True
):
    if not TOKEN_FILE.exists():
        return None

    try:
        return Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    except (OSError, ValueError):
        if emit_errors:
            emit(
                "Google token.json повреждён или не подходит. "
                "Нужна повторная авторизация.",
                status_callback
            )

        TOKEN_FILE.unlink(missing_ok=True)
        return None


def has_saved_google_login() -> bool:
    creds = load_saved_credentials(
        emit_errors=False
    )

    return bool(
        creds and (
            creds.valid or creds.refresh_token
        )
    )


def save_credentials(creds) -> None:
    TOKEN_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        TOKEN_FILE,
        "w",
        encoding="utf-8"
    ) as token:
        token.write(creds.to_json())


def get_calendar_service(
    status_callback: StatusCallback | None = None
):
    creds = load_saved_credentials(status_callback=status_callback)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())

            except RefreshError:
                emit(
                    "Старый Google token.json недействителен. "
                    "Нужна повторная авторизация.",
                    status_callback
                )

                TOKEN_FILE.unlink(missing_ok=True)
                creds = None

        if not creds or not creds.valid:
            emit(
                "Открываю авторизацию Google",
                status_callback
            )

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

        save_credentials(creds)

        emit("Google token.json сохранён", status_callback)

    service = build(
        "calendar",
        "v3",
        credentials=creds
    )

    return service