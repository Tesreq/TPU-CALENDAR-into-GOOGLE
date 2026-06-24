import unittest
from unittest.mock import patch

from app import calendar_manager
from app import delete_tpu_calendar


class FakeRequest:
    def __init__(self, result=None):
        self.result = result

    def execute(self):
        return self.result


class FakeCalendarListResource:
    def __init__(self, service):
        self.service = service

    def list(self, **kwargs):
        self.service.calendar_list_calls.append(kwargs)
        return FakeRequest({"items": self.service.calendar_list_items})


class FakeCalendarsResource:
    def __init__(self, service):
        self.service = service

    def get(self, calendarId):
        self.service.get_calls.append(calendarId)
        return FakeRequest(self.service.calendars_by_id.get(calendarId))

    def insert(self, body):
        self.service.insert_calls.append(body)
        created = {"id": "created-calendar-id", **body}
        self.service.calendars_by_id[created["id"]] = created
        return FakeRequest(created)

    def delete(self, calendarId):
        self.service.delete_calls.append(calendarId)
        self.service.calendars_by_id.pop(calendarId, None)
        return FakeRequest({})


class FakeService:
    def __init__(self, calendars=None, calendar_list_items=None):
        calendars = calendars or {}
        self.calendars_by_id = dict(calendars)
        self.calendar_list_items = list(calendar_list_items or calendars.values())
        self.get_calls = []
        self.insert_calls = []
        self.delete_calls = []
        self.calendar_list_calls = []

    def calendars(self):
        return FakeCalendarsResource(self)

    def calendarList(self):
        return FakeCalendarListResource(self)


class CalendarIdTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "calendar_name": "TPU Schedule",
            "timezone": "Asia/Tomsk",
            "calendar_id": ""
        }
        self.saved_configs = []
        self.config_patch = patch.object(calendar_manager, "CONFIG", self.config)
        self.delete_config_patch = patch.object(delete_tpu_calendar, "CONFIG", self.config)
        self.save_patch = patch.object(
            calendar_manager,
            "save_config",
            side_effect=self.save_config
        )
        self.config_patch.start()
        self.delete_config_patch.start()
        self.save_patch.start()

    def tearDown(self) -> None:
        self.save_patch.stop()
        self.delete_config_patch.stop()
        self.config_patch.stop()

    def save_config(self, config: dict) -> None:
        self.config.clear()
        self.config.update(config)
        self.saved_configs.append(dict(config))

    def test_uses_matching_saved_calendar_id_before_name_search(self) -> None:
        self.config["calendar_id"] = "saved-id"
        service = FakeService(
            calendars={
                "saved-id": {
                    "id": "saved-id",
                    "summary": "TPU Schedule"
                }
            }
        )

        calendar_id = calendar_manager.get_or_create_calendar(
            service=service,
            status_callback=lambda _message: None
        )

        self.assertEqual(calendar_id, "saved-id")
        self.assertEqual(service.get_calls, ["saved-id"])
        self.assertEqual(service.calendar_list_calls, [])
        self.assertEqual(service.insert_calls, [])

    def test_ignores_saved_calendar_id_when_calendar_name_changed(self) -> None:
        self.config["calendar_id"] = "saved-id"
        messages = []
        service = FakeService(
            calendars={
                "saved-id": {
                    "id": "saved-id",
                    "summary": "Old TPU Schedule"
                }
            },
            calendar_list_items=[
                {"id": "new-id", "summary": "TPU Schedule"}
            ]
        )

        calendar_id = calendar_manager.get_or_create_calendar(
            service=service,
            status_callback=messages.append
        )

        self.assertEqual(calendar_id, "new-id")
        self.assertEqual(self.config["calendar_id"], "new-id")
        self.assertEqual(service.get_calls, ["saved-id"])
        self.assertEqual(service.insert_calls, [])
        self.assertTrue(
            any("calendar_id" in message for message in messages)
        )

    def test_saves_id_when_existing_calendar_is_found_by_name(self) -> None:
        service = FakeService(
            calendar_list_items=[
                {"id": "existing-id", "summary": "TPU Schedule"}
            ]
        )

        calendar_id = calendar_manager.get_or_create_calendar(
            service=service,
            status_callback=lambda _message: None
        )

        self.assertEqual(calendar_id, "existing-id")
        self.assertEqual(self.config["calendar_id"], "existing-id")
        self.assertEqual(service.insert_calls, [])

    def test_saves_id_when_calendar_is_created(self) -> None:
        service = FakeService(calendar_list_items=[])

        calendar_id = calendar_manager.get_or_create_calendar(
            service=service,
            status_callback=lambda _message: None
        )

        self.assertEqual(calendar_id, "created-calendar-id")
        self.assertEqual(self.config["calendar_id"], "created-calendar-id")
        self.assertEqual(
            service.insert_calls,
            [{"summary": "TPU Schedule", "timeZone": "Asia/Tomsk"}]
        )

    def test_delete_uses_saved_calendar_id_and_clears_config(self) -> None:
        self.config["calendar_id"] = "saved-id"
        service = FakeService(
            calendars={
                "saved-id": {
                    "id": "saved-id",
                    "summary": "TPU Schedule"
                }
            }
        )

        with patch.object(
            delete_tpu_calendar,
            "get_calendar_service",
            return_value=service
        ):
            deleted = delete_tpu_calendar.delete_calendar(
                status_callback=lambda _message: None
            )

        self.assertTrue(deleted)
        self.assertEqual(service.delete_calls, ["saved-id"])
        self.assertEqual(self.config["calendar_id"], "")


if __name__ == "__main__":
    unittest.main()