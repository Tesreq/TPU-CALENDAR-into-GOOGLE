from app_logging import StatusCallback
from delete_tpu_calendar import delete_calendar
from manage_subjects import load_subjects, save_subjects
from sync_calendar import sync_calendar
from sync_to_json import update_schedule


def full_sync(
    status_callback: StatusCallback | None = None
) -> dict:
    schedule_result = update_schedule(status_callback=status_callback)
    calendar_result = sync_calendar(status_callback=status_callback)

    return {
        "schedule": schedule_result,
        "calendar": calendar_result
    }
