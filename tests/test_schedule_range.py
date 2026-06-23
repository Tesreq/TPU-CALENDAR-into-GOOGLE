import unittest

from app.sync_calendar import get_calendar_cleanup_date_range
from app.sync_to_json import get_schedule_date_range


class ScheduleRangeTests(unittest.TestCase):
    def test_schedule_date_range_covers_requested_weeks(self) -> None:
        self.assertEqual(
            get_schedule_date_range(2025, start_week=1, weeks_count=2),
            ("2025-09-01", "2025-09-14")
        )

    def test_cleanup_uses_explicit_sync_range_even_without_lessons(self) -> None:
        schedule = {
            "sync_range": {
                "start": "2025-09-01",
                "end": "2025-09-14"
            }
        }

        self.assertEqual(
            get_calendar_cleanup_date_range(schedule, []),
            ("2025-09-01", "2025-09-14")
        )

    def test_cleanup_falls_back_to_lesson_dates_for_old_json(self) -> None:
        lessons = [
            {"date": "2025-09-03"},
            {"date": "2025-09-08"}
        ]

        self.assertEqual(
            get_calendar_cleanup_date_range({}, lessons),
            ("2025-09-03", "2025-09-08")
        )


if __name__ == "__main__":
    unittest.main()