from .app_logging import StatusCallback, emit
from .calendar_api import get_calendar_service
from .config import CONFIG


def delete_calendar(
    status_callback: StatusCallback | None = None
) -> bool:
    calendar_name = CONFIG["calendar_name"]

    service = get_calendar_service(status_callback=status_callback)

    calendars = (
        service
        .calendarList()
        .list()
        .execute()
    )

    found = False

    for calendar in calendars.get("items", []):
        if calendar["summary"] == calendar_name:
            calendar_id = calendar["id"]

            (
                service
                .calendars()
                .delete(calendarId=calendar_id)
                .execute()
            )

            emit(
                f"Календарь удалён: {calendar_name}",
                status_callback
            )

            return True

    emit(
        f"Календарь не найден: {calendar_name}",
        status_callback
    )

    return False


if __name__ == "__main__":
    delete_calendar()
