import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app_logging


class AppLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_handlers = list(app_logging.logger.handlers)
        app_logging.logger.handlers.clear()
        app_logging._file_logging_configured = False
        app_logging._file_logging_failed = False

    def tearDown(self) -> None:
        for handler in app_logging.logger.handlers:
            handler.close()
        app_logging.logger.handlers.clear()
        app_logging.logger.handlers.extend(self.old_handlers)
        app_logging._file_logging_configured = False
        app_logging._file_logging_failed = False

    def test_import_does_not_configure_file_handler(self) -> None:
        self.assertEqual(app_logging.logger.handlers, [])
        self.assertFalse(app_logging._file_logging_configured)

    def test_emit_configures_file_logging_lazily(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            with patch.object(app_logging, "LOGS_DIR", log_dir), patch.object(
                app_logging,
                "LOG_FILE",
                log_dir / "sync.log"
            ):
                app_logging.emit("hello", status_callback=lambda _message: None)

            self.assertTrue((log_dir / "sync.log").exists())
            self.assertTrue(app_logging._file_logging_configured)

            for handler in app_logging.logger.handlers:
                handler.close()
            app_logging.logger.handlers.clear()
            app_logging._file_logging_configured = False


if __name__ == "__main__":
    unittest.main()