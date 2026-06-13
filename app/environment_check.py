from dataclasses import dataclass

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from .config import (
    CREDENTIALS_FILE,
    PARSED_SCHEDULE_FILE,
    SUBJECTS_FILE,
    TOKEN_FILE
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


def check_environment(
    include_browser: bool = False
) -> list[EnvironmentStatus]:
    statuses = [
        EnvironmentStatus(
            key="credentials",
            title="Google credentials",
            ok=CREDENTIALS_FILE.exists(),
            message=(
                "credentials.json найден"
                if CREDENTIALS_FILE.exists()
                else "credentials.json не найден"
            )
        ),
        EnvironmentStatus(
            key="token",
            title="Google token",
            ok=TOKEN_FILE.exists(),
            message=(
                "token.json найден"
                if TOKEN_FILE.exists()
                else "token.json появится после входа"
            )
        ),
        EnvironmentStatus(
            key="schedule",
            title="Расписание",
            ok=PARSED_SCHEDULE_FILE.exists(),
            message=(
                "parsed_schedule.json найден"
                if PARSED_SCHEDULE_FILE.exists()
                else "обновите расписание"
            )
        ),
        EnvironmentStatus(
            key="subjects",
            title="Предметы",
            ok=SUBJECTS_FILE.exists(),
            message=(
                "subjects.json найден"
                if SUBJECTS_FILE.exists()
                else "обновите расписание"
            )
        )
    ]

    if include_browser:
        statuses.append(check_playwright_chromium())

    return statuses
