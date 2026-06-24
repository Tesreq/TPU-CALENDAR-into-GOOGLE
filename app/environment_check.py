from dataclasses import dataclass

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

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


def check_playwright_chromium() -> EnvironmentStatus:
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()

    except PlaywrightError:
        return EnvironmentStatus(
            key="playwright",
            title="Playwright",
            ok=False,
            message="Chromium не установлен"
        )

    return EnvironmentStatus(
        key="playwright",
        title="Playwright",
        ok=True,
        message="Chromium доступен"
    )


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


def check_environment(
    include_browser: bool = False
) -> list[EnvironmentStatus]:
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

    if include_browser:
        statuses.append(check_playwright_chromium())

    return statuses