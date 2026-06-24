from googleapiclient.errors import HttpError

from .app_logging import StatusCallback, emit
from .calendar_api import get_calendar_service
from .config import CONFIG, save_config


NOT_FOUND_STATUSES = {404, 410}


def save_calendar_id(calendar_id: str) -> None:
    save_config({
        **CONFIG,
        "calendar_id": calendar_id
    })


def clear_calendar_id() -> None:
    if CONFIG.get("calendar_id"):
        save_calendar_id("")


def is_not_found_error(error: HttpError) -> bool:
    return getattr(error.resp, "status", None) in NOT_FOUND_STATUSES


def get_calendar_by_id(service, calendar_id: str) -> dict | None:
    if not calendar_id:
        return None

    try:
        return (
            service
            .calendars()
            .get(calendarId=calendar_id)
            .execute()
        )

    except HttpError as error:
        if is_not_found_error(error):
            return None

        raise


def list_calendars(service) -> list[dict]:
    calendars = []
    page_token = None

    while True:
        result = (
            service
            .calendarList()
            .list(pageToken=page_token)
            .execute()
        )
        calendars.extend(result.get("items", []))
        page_token = result.get("nextPageToken")

        if not page_token:
            break

    return calendars


def find_calendar_by_name(service, calendar_name: str) -> dict | None:
    matches = [
        calendar
        for calendar in list_calendars(service)
        if calendar.get("summary") == calendar_name
    ]

    if len(matches) > 1:
        raise ValueError(
            f"Найдено несколько календарей с именем {calendar_name}. "
            "Переименуйте лишние календари или укажите другое имя календаря."
        )

    if not matches:
        return None

    return matches[0]


def calendar_matches_name(calendar: dict, calendar_name: str) -> bool:
    return calendar.get("summary") == calendar_name


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

    saved_calendar_id = CONFIG.get("calendar_id", "").strip()
    saved_calendar = get_calendar_by_id(
        service,
        saved_calendar_id
    )

    if saved_calendar:
        saved_summary = saved_calendar.get("summary", "")

        if calendar_matches_name(saved_calendar, calendar_name):
            emit(
                f"Найден календарь: {saved_summary or calendar_name}",
                status_callback
            )
            return saved_calendar_id

        saved_calendar_label = saved_summary or saved_calendar_id
        clear_calendar_id()
        saved_calendar_id = ""
        emit(
            "Сохранённый Google calendar_id относится к календарю "
            f'"{saved_calendar_label}", а в настройках указан '
            f'"{calendar_name}". Ищу календарь заново.',
            status_callback
        )

    if saved_calendar_id:
        clear_calendar_id()
        emit(
            "Сохранённый Google calendar_id недействителен. "
            "Ищу календарь заново.",
            status_callback
        )

    existing_calendar = find_calendar_by_name(
        service,
        calendar_name
    )

    if existing_calendar:
        calendar_id = existing_calendar["id"]
        save_calendar_id(calendar_id)
        emit(
            f"Найден календарь: {calendar_name}",
            status_callback
        )
        return calendar_id

    new_calendar = {
        "summary": calendar_name,
        "timeZone": timezone
    }

    created_calendar = (
        service
        .calendars()
        .insert(body=new_calendar)
        .execute()
    )
    calendar_id = created_calendar["id"]
    save_calendar_id(calendar_id)

    emit(
        f"Создан календарь: {calendar_name}",
        status_callback
    )

    return calendar_id
