import unittest
from pathlib import Path

from app.parser import ScheduleParseError, parse_schedule


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class ParseScheduleTests(unittest.TestCase):
    def test_parse_basic_week_fixture(self) -> None:
        lessons = parse_schedule(load_fixture("basic_week.html"))

        self.assertEqual(
            lessons,
            [
                {
                    "date": "2025-09-01",
                    "start": "08:30",
                    "end": "10:05",
                    "title": "Высшая математика",
                    "type": "ЛК",
                    "teacher": "Иванов И.И.",
                    "location": "к. 10 201"
                },
                {
                    "date": "2025-09-02",
                    "start": "10:25",
                    "end": "12:00",
                    "title": "Проектная деятельность",
                    "type": "",
                    "teacher": "",
                    "location": ""
                }
            ]
        )

    def test_parse_multiple_lessons_split_by_hr(self) -> None:
        lessons = parse_schedule(load_fixture("split_lessons.html"))

        self.assertEqual(len(lessons), 2)
        self.assertEqual(
            [lesson["title"] for lesson in lessons],
            ["Физика", "Английский язык"]
        )
        self.assertEqual(
            [lesson["type"] for lesson in lessons],
            ["ЛБ", "ПР"]
        )
        self.assertTrue(
            all(lesson["date"] == "2025-09-03" for lesson in lessons)
        )
        self.assertEqual(lessons[0]["location"], "к. 2 15")
        self.assertEqual(lessons[1]["teacher"], "Сидорова А.А.")

    def test_missing_schedule_table_raises_parse_error(self) -> None:
        with self.assertRaises(ScheduleParseError):
            parse_schedule(load_fixture("missing_table.html"))


if __name__ == "__main__":
    unittest.main()