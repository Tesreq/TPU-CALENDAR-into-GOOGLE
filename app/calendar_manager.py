from .app_logging import StatusCallback, emit
from .calendar_api import get_calendar_service
from .config import CONFIG


def get_or_create_calendar(
    service=None,
    status_callback: StatusCallback | None = None
) -> str:
    calendar_name = CONFIG["calendar_name"]
    timezone = CONFIG["timezone"]

    if service is None:
        service = get_calendar_service(
            status_callback=status_callback
        )

    calendars = service.calendarList().list().execute()

    for calendar in calendars.get("items", []):
        if calendar["summary"] == calendar_name:
            emit(
                f"Найден календарь: {calendar_name}",
                status_callback
            )
            return calendar["id"]

    new_calendar = {
        "summary": calendar_name,
        "timeZone": timezone
    }

    created_calendar = service.calendars().insert(
        body=new_calendar
    ).execute()

    emit(
        f"Создан календарь: {calendar_name}",
        status_callback
    )

    return created_calendar["id"]
