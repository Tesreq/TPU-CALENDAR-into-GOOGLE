from app_logging import StatusCallback, emit
from calendar_api import get_calendar_service
from config import CONFIG


CALENDAR_NAME = CONFIG["calendar_name"]
TIMEZONE = CONFIG["timezone"]


def get_or_create_calendar(
    service=None,
    status_callback: StatusCallback | None = None
) -> str:
    if service is None:
        service = get_calendar_service(
            status_callback=status_callback
        )

    calendars = service.calendarList().list().execute()

    for calendar in calendars.get("items", []):
        if calendar["summary"] == CALENDAR_NAME:
            emit(
                f"Найден календарь: {CALENDAR_NAME}",
                status_callback
            )
            return calendar["id"]

    new_calendar = {
        "summary": CALENDAR_NAME,
        "timeZone": TIMEZONE
    }

    created_calendar = service.calendars().insert(
        body=new_calendar
    ).execute()

    emit(
        f"Создан календарь: {CALENDAR_NAME}",
        status_callback
    )

    return created_calendar["id"]
