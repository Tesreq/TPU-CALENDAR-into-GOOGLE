import hashlib
import json
from datetime import datetime

from .app_logging import StatusCallback, emit
from .config import CONFIG, PARSED_SCHEDULE_FILE, SUBJECTS_FILE
from .group_search import resolve_group_id
from .parser import (
    get_current_study_week,
    build_schedule_url,
    fetch_rendered_html_many,
    parse_schedule
)


def make_lesson_id(lesson: dict) -> str:
    raw = "|".join([
        lesson["date"],
        lesson["start"],
        lesson["end"],
        lesson["title"],
        lesson["type"],
    ])

    return "tpu" + hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:40]


def load_existing_subjects() -> dict:
    if not SUBJECTS_FILE.exists():
        return {}

    with open(
        SUBJECTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        subjects = json.load(file)

    return {
        subject["title"]: subject
        for subject in subjects
    }


def save_json(filename: str, data) -> None:
    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


def update_schedule(
    status_callback: StatusCallback | None = None
) -> dict:
    group_name = CONFIG["group_name"]
    study_year = CONFIG["study_year"]
    weeks_ahead = CONFIG["weeks_ahead"]

    emit(f"Ищу группу: {group_name}", status_callback)

    group_id = resolve_group_id(
        group_name,
        status_callback=status_callback
    )

    if not group_id:
        raise ValueError(
            f"Не удалось найти группу: {group_name}"
        )

    emit(f"Группа найдена, id: {group_id}", status_callback)

    current_week = get_current_study_week(
        datetime.today().date(),
        study_year
    )

    all_lessons = []

    week_urls = {}

    for week in range(
        current_week,
        current_week + weeks_ahead
    ):
        url = build_schedule_url(
            group_id,
            study_year,
            week
        )

        week_urls[week] = url

    html_by_url = fetch_rendered_html_many(
        list(week_urls.values()),
        status_callback=status_callback
    )

    for week, url in week_urls.items():
        html = html_by_url[url]

        lessons = parse_schedule(
            html,
            status_callback=status_callback
        )

        emit(
            f"Неделя {week}: найдено занятий "
            f"{len(lessons)}",
            status_callback
        )

        for lesson in lessons:
            lesson["id"] = make_lesson_id(lesson)
            lesson["week"] = week

            all_lessons.append(lesson)

    unique_lessons = {}

    for lesson in all_lessons:
        unique_lessons[lesson["id"]] = lesson

    lessons_result = list(
        unique_lessons.values()
    )

    schedule_data = {
        "university": "tpu",
        "group_name": group_name,
        "group_id": group_id,
        "study_year": study_year,
        "updated_at": datetime.now().isoformat(
            timespec="seconds"
        ),
        "lessons": lessons_result
    }

    save_json(
        PARSED_SCHEDULE_FILE,
        schedule_data
    )

    existing_subjects = (
        load_existing_subjects()
    )

    titles = sorted(
        set(
            lesson["title"]
            for lesson in lessons_result
        )
    )

    subjects_result = []

    for title in titles:
        old_subject = (
            existing_subjects.get(title)
        )

        subjects_result.append({
            "title": title,
            "enabled": (
                old_subject["enabled"]
                if old_subject
                else True
            )
        })

    save_json(
        SUBJECTS_FILE,
        subjects_result
    )

    emit(
        f"Расписание сохранено: {len(lessons_result)} занятий",
        status_callback
    )

    emit(
        f"Предметов найдено: {len(subjects_result)}",
        status_callback
    )

    return {
        "schedule": schedule_data,
        "subjects": subjects_result,
        "lessons_count": len(lessons_result),
        "subjects_count": len(subjects_result),
        "schedule_file": PARSED_SCHEDULE_FILE,
        "subjects_file": SUBJECTS_FILE
    }


def main():
    result = update_schedule()

    print("\nГотово")

    print(
        "Занятий сохранено:",
        result["lessons_count"]
    )

    print(
        "Предметов найдено:",
        result["subjects_count"]
    )

    print(
        "Файл расписания:",
        result["schedule_file"].name
    )

    print(
        "Файл предметов:",
        result["subjects_file"].name
    )


if __name__ == "__main__":
    main()
