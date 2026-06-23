import unittest

from app.sync_to_json import make_lesson_id


BASE_LESSON = {
    "date": "2025-09-01",
    "start": "08:30",
    "end": "10:05",
    "title": "Высшая математика",
    "type": "ЛК",
    "teacher": "Иванов И.И.",
    "location": "к. 10 201"
}


class LessonIdTests(unittest.TestCase):
    def test_id_changes_for_parallel_lessons_in_same_slot(self) -> None:
        first = {
            **BASE_LESSON,
            "teacher": "Иванов И.И.",
            "location": "к. 10 201"
        }
        second = {
            **BASE_LESSON,
            "teacher": "Петров П.П.",
            "location": "к. 10 202"
        }

        self.assertNotEqual(
            make_lesson_id(first, group_name="8И31", study_year=2025),
            make_lesson_id(second, group_name="8И31", study_year=2025)
        )

    def test_id_includes_group_context(self) -> None:
        self.assertNotEqual(
            make_lesson_id(BASE_LESSON, group_name="8И31", study_year=2025),
            make_lesson_id(BASE_LESSON, group_name="8И32", study_year=2025)
        )

    def test_id_is_stable_for_whitespace_and_case_noise(self) -> None:
        noisy_lesson = {
            "date": "2025-09-01",
            "start": "08:30",
            "end": "10:05",
            "title": "  ВЫСШАЯ   МАТЕМАТИКА  ",
            "type": " лк ",
            "teacher": " Иванов   И.И. ",
            "location": " к. 10   201 "
        }

        self.assertEqual(
            make_lesson_id(BASE_LESSON, group_name=" 8и31 ", study_year=2025),
            make_lesson_id(noisy_lesson, group_name="8И31", study_year=2025)
        )

    def test_id_uses_google_calendar_safe_shape(self) -> None:
        lesson_id = make_lesson_id(
            BASE_LESSON,
            group_name="8И31",
            study_year=2025
        )

        self.assertEqual(len(lesson_id), 44)
        self.assertTrue(lesson_id.startswith("tpu2"))
        self.assertRegex(lesson_id, r"^[a-v0-9]+$")


if __name__ == "__main__":
    unittest.main()