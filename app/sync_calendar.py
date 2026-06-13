import json

from googleapiclient.errors import HttpError

from .app_logging import StatusCallback, emit
from .calendar_api import get_calendar_service
from .calendar_manager import get_or_create_calendar
from .config import CONFIG, PARSED_SCHEDULE_FILE, SUBJECTS_FILE


TIMEZONE = CONFIG["timezone"]
LESSON_COLORS = {
    "ЛК": "9",
    "ПР": "10",
    "ЛБ": "11"
}

DEFAULT_COLOR = "8"

def load_json(filename: str):
    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def load_enabled_subjects() -> set[str]:
    subjects = load_json(SUBJECTS_FILE)

    return {
        subject["title"]
        for subject in subjects
        if subject.get("enabled", True)
    }


def load_lessons() -> list[dict]:
    schedule = load_json(PARSED_SCHEDULE_FILE)

    return schedule["lessons"]


def lesson_to_event(lesson: dict) -> dict:
    title = lesson["title"]

    if lesson["type"]:
        title = f'{title} ({lesson["type"]})'

    description_parts = []

    if lesson["teacher"]:
        description_parts.append(
            f'Преподаватель: {lesson["teacher"]}'
        )

    description_parts.append(
        "Источник: расписание ТПУ"
    )
    lesson_type = lesson["type"]

    color_id = LESSON_COLORS.get(
        lesson_type,
        DEFAULT_COLOR
    )
    return {
        "id": lesson["id"],

        "summary": title,

        "colorId": color_id,

        "location": lesson["location"],

        "description": "\n".join(
            description_parts
        ),

        "start": {
            "dateTime": (
                f'{lesson["date"]}T'
                f'{lesson["start"]}:00'
            ),
            "timeZone": TIMEZONE
        },

        "end": {
            "dateTime": (
                f'{lesson["date"]}T'
                f'{lesson["end"]}:00'
            ),
            "timeZone": TIMEZONE
        },

        "extendedProperties": {
            "private": {
                "lesson_id": lesson["id"],
                "source": "tpu_schedule_sync"
            }
        }
    }


def upsert_calendar_event(
    service,
    calendar_id: str,
    lesson: dict
) -> str:

    event = lesson_to_event(lesson)

    try:
        service.events().insert(
            calendarId=calendar_id,
            body=event
        ).execute()

        return "created"

    except HttpError as error:
        if error.resp.status == 409:
            service.events().update(
                calendarId=calendar_id,
                eventId=lesson["id"],
                body=event
            ).execute()

            return "updated"

        raise


def get_all_tpu_events(
    service,
    calendar_id: str
) -> list[dict]:

    events = []
    page_token = None

    while True:
        result = service.events().list(
            calendarId=calendar_id,
            privateExtendedProperty="source=tpu_schedule_sync",
            maxResults=2500,
            pageToken=page_token
        ).execute()

        events.extend(
            result.get("items", [])
        )

        page_token = result.get("nextPageToken")

        if not page_token:
            break

    return events


def delete_removed_events(
    service,
    calendar_id: str,
    current_lesson_ids: set[str],
    status_callback: StatusCallback | None = None
) -> int:

    deleted_count = 0

    events = get_all_tpu_events(
        service,
        calendar_id
    )

    for event in events:
        event_id = event["id"]

        if event_id not in current_lesson_ids:
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            emit(
                "Удалено: "
                f"{event.get('summary', event_id)}",
                status_callback
            )

            deleted_count += 1

    return deleted_count


def sync_calendar(
    status_callback: StatusCallback | None = None
) -> dict:
    all_lessons = load_lessons()
    enabled_subjects = load_enabled_subjects()

    filtered_lessons = [
        lesson
        for lesson in all_lessons
        if lesson["title"] in enabled_subjects
    ]

    unique_lessons = {
        lesson["id"]: lesson
        for lesson in filtered_lessons
    }

    current_lesson_ids = set(
        unique_lessons.keys()
    )

    emit(
        f"Всего занятий в JSON: "
        f"{len(all_lessons)}",
        status_callback
    )

    emit(
        f"Выбрано для календаря: "
        f"{len(unique_lessons)}",
        status_callback
    )

    service = get_calendar_service(status_callback=status_callback)
    calendar_id = get_or_create_calendar(
        service=service,
        status_callback=status_callback
    )

    created_count = 0
    updated_count = 0

    for lesson in unique_lessons.values():
        status = upsert_calendar_event(
            service,
            calendar_id,
            lesson
        )

        if status == "created":
            emit(
                "Создано: "
                f"{lesson['date']} "
                f"{lesson['start']} "
                f"{lesson['title']}",
                status_callback
            )

            created_count += 1

        elif status == "updated":
            emit(
                "Обновлено: "
                f"{lesson['date']} "
                f"{lesson['start']} "
                f"{lesson['title']}",
                status_callback
            )

            updated_count += 1

    deleted_count = delete_removed_events(
        service,
        calendar_id,
        current_lesson_ids,
        status_callback=status_callback
    )

    emit(
        "Синхронизация завершена: "
        f"создано {created_count}, "
        f"обновлено {updated_count}, "
        f"удалено {deleted_count}",
        status_callback
    )

    return {
        "all_lessons_count": len(all_lessons),
        "selected_lessons_count": len(unique_lessons),
        "created_count": created_count,
        "updated_count": updated_count,
        "deleted_count": deleted_count,
        "calendar_id": calendar_id
    }


def main():
    result = sync_calendar()

    print("\nГотово")
    print("Создано:", result["created_count"])
    print("Обновлено:", result["updated_count"])
    print("Удалено:", result["deleted_count"])


if __name__ == "__main__":
    main()
