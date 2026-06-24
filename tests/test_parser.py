import unittest
from pathlib import Path
from unittest.mock import patch

from app.parser import (
    ScheduleParseError,
    decrypt_schedule_html,
    parse_schedule
)


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

    def test_parse_nested_time_and_auditorium_location(self) -> None:
        lessons = parse_schedule(load_fixture("weird_markup.html"))

        self.assertEqual(
            lessons,
            [
                {
                    "date": "2025-09-04",
                    "start": "08:30",
                    "end": "10:05",
                    "title": "Информатика",
                    "type": "ПР",
                    "teacher": "Смирнов С.С.",
                    "location": "ауд. 301"
                }
            ]
        )

    def test_missing_schedule_table_raises_parse_error(self) -> None:
        with self.assertRaises(ScheduleParseError):
            parse_schedule(load_fixture("missing_table.html"))

    def test_decrypts_tpu_encrypted_subject_title(self) -> None:
        html = """
        <html>
          <head><meta name="encrypt" content="token"></head>
          <body data-absolute_url="https://ro-rasp.tpu.ru">
            <table id="raspisanie-table">
              <thead>
                <tr><th></th><th>22.06.26 ПН</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>08:30 - 10:05</td>
                  <td class="cell">
                    <div>
                      <span
                        class="encrypt"
                        data-encrypt="0YbRq9CQTNCO0afRs9CwY9Cv0Zk="
                      ></span>
                      (<b title="Экзамен">Э</b>)
                    </div>
                    <div>Мирошниченко Е. А.</div>
                    <div>к. 10, ауд. 406</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </body>
        </html>
        """

        with patch(
            "app.parser.fetch_decryption_key",
            return_value="ZS1lNWDpM7x6jAKw"
        ):
            decrypted_html = decrypt_schedule_html(
                html,
                "https://ro-rasp.tpu.ru/gruppa_40908/2025/43/view.html"
            )

        lessons = parse_schedule(decrypted_html)

        self.assertEqual(lessons[0]["title"], "МиС разр.ИС")
        self.assertEqual(lessons[0]["type"], "Э")


if __name__ == "__main__":
    unittest.main()
