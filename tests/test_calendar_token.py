import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import calendar_api


class CalendarTokenTests(unittest.TestCase):
    def test_load_saved_credentials_removes_invalid_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            token_file = Path(temp_dir) / "token.json"
            token_file.write_text("not json", encoding="utf-8")
            messages = []

            with patch.object(calendar_api, "TOKEN_FILE", token_file):
                creds = calendar_api.load_saved_credentials(messages.append)

            self.assertIsNone(creds)
            self.assertFalse(token_file.exists())
            self.assertTrue(
                any("token.json повреждён" in message for message in messages)
            )

    def test_has_saved_google_login_removes_invalid_token_silently(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            token_file = Path(temp_dir) / "token.json"
            token_file.write_text("not json", encoding="utf-8")

            with patch.object(calendar_api, "TOKEN_FILE", token_file):
                self.assertFalse(calendar_api.has_saved_google_login())

            self.assertFalse(token_file.exists())

    def test_load_saved_credentials_returns_none_when_token_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            token_file = Path(temp_dir) / "token.json"

            with patch.object(calendar_api, "TOKEN_FILE", token_file):
                self.assertIsNone(calendar_api.load_saved_credentials())


if __name__ == "__main__":
    unittest.main()