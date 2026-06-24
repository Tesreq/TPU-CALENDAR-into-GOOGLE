from dataclasses import dataclass


from .calendar_api import has_saved_google_login
from .config import (
    CREDENTIALS_FILE,
    PARSED_SCHEDULE_FILE,
    SUBJECTS_FILE
)


@dataclass
class EnvironmentStatus:
    key: str
    title: str
    ok: bool
    message: str


def check_google_token() -> EnvironmentStatus:
    has_login = has_saved_google_login()

    return EnvironmentStatus(
        key="token",
        title="Google token",
        ok=has_login,
        message=(
            "Успешный вход в аккаунт Google"
            if has_login
            else "Вход в Google не выполнен"
        )
    )


def check_environment() -> list[EnvironmentStatus]:
    statuses = [
        EnvironmentStatus(
            key="credentials",
            title="Google credentials",
            ok=CREDENTIALS_FILE.exists(),
            message=(
                "credentials.json найден, можно войти"
                if CREDENTIALS_FILE.exists()
                else "credentials.json не найден"
            )
        ),
        check_google_token(),
        EnvironmentStatus(
            key="schedule",
            title="Расписание",
            ok=PARSED_SCHEDULE_FILE.exists(),
            message=(
                "Загружено"
                if PARSED_SCHEDULE_FILE.exists()
                else "Не загружено"
            )
        ),
        EnvironmentStatus(
            key="subjects",
            title="Предметы",
            ok=SUBJECTS_FILE.exists(),
            message=(
                "Список загружен"
                if SUBJECTS_FILE.exists()
                else "Список не загружен"
            )
        )
    ]

    return statuses