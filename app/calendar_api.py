from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import os.path

from app_logging import StatusCallback, emit
from config import CREDENTIALS_FILE, TOKEN_FILE


SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]


def get_calendar_service(
    status_callback: StatusCallback | None = None
):
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

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

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

        emit("Google token.json сохранён", status_callback)

    service = build(
        "calendar",
        "v3",
        credentials=creds
    )

    return service
