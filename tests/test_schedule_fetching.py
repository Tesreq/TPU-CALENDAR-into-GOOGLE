import unittest
from pathlib import Path
from unittest.mock import patch

from app import parser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class FakeResponse:
    def __init__(self, text: str):
        self.text = text
        self.encoding = "utf-8"

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.get_calls = []

    def get(self, *args, **kwargs):
        self.get_calls.append((args, kwargs))
        return self.response


class ScheduleFetchingTests(unittest.TestCase):
    def test_fetch_schedule_html_uses_static_html_when_table_exists(self) -> None:
        html = load_fixture("basic_week.html")
        messages = []
        session = FakeSession(FakeResponse(html))

        with patch.object(
            parser.requests,
            "Session",
            return_value=session
        ):
            result = parser.fetch_schedule_html(
                "https://example.test/schedule.html",
                status_callback=messages.append
            )

        self.assertEqual(result, html)
        self.assertEqual(len(session.get_calls), 1)
        self.assertTrue(
            any("Загружаю расписание" in message for message in messages)
        )

    def test_fetch_schedule_html_raises_when_table_is_missing(self) -> None:
        html = load_fixture("missing_table.html")
        messages = []
        session = FakeSession(FakeResponse(html))

        with patch.object(
            parser.requests,
            "Session",
            return_value=session
        ):
            with self.assertRaises(parser.ScheduleParseError):
                parser.fetch_schedule_html(
                    "https://example.test/schedule.html",
                    status_callback=messages.append
                )


if __name__ == "__main__":
    unittest.main()
