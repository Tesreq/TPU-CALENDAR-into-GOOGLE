from googleapiclient.errors import HttpError

from .app_logging import StatusCallback, emit
from .calendar_api import get_calendar_service
from .config import CONFIG
from .calendar_manager import (
    clear_calendar_id,
    find_calendar_by_name,
    get_calendar_by_id,
    is_not_found_error,
    save_calendar_id
)


def delete_calendar(
    status_callback: StatusCallback | None = None
) -> bool:
    calendar_name = CONFIG["calendar_name"]
    calendar_id = CONFIG.get("calendar_id", "").strip()

    service = get_calendar_service(status_callback=status_callback)

    if calendar_id:
        calendar = get_calendar_by_id(service, calendar_id)

        if calendar:
            try:
                (
                    service
                    .calendars()
                    .delete(calendarId=calendar_id)
                    .execute()
                )

            except HttpError as error:
                if not is_not_found_error(error):
                    raise

            clear_calendar_id()
            emit(
                f"Календарь удалён: {calendar.get('summary', calendar_name)}",
                status_callback
            )
            return True

        clear_calendar_id()
        emit(
            "Сохранённый Google calendar_id недействителен. "
            "Ищу календарь по имени.",
            status_callback
        )

    calendar = find_calendar_by_name(
        service,
        calendar_name
    )

    if not calendar:
        emit(
            f"Календарь не найден: {calendar_name}",
            status_callback
        )
        return False

    calendar_id = calendar["id"]
    save_calendar_id(calendar_id)

    (
        service
        .calendars()
        .delete(calendarId=calendar_id)
        .execute()
    )
    clear_calendar_id()

    emit(
        f"Календарь удалён: {calendar_name}",
        status_callback
    )

    return True


if __name__ == "__main__":
    delete_calendar()
