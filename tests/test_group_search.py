import unittest
from unittest.mock import patch

from app.group_search import (
    normalize_group_name,
    result_matches_group,
    search_group,
    select_group_result
)


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


class GroupSearchTests(unittest.TestCase):
    def test_normalize_group_name_accepts_latin_i(self) -> None:
        self.assertEqual(normalize_group_name(" 8i31 "), "8И31")

    def test_result_matches_exact_group_token(self) -> None:
        self.assertTrue(
            result_matches_group(
                {"text": "8И31 Институт"},
                "8i31"
            )
        )

    def test_select_group_result_skips_similar_first_result(self) -> None:
        results = [
            {"text": "8И310", "url": "/wrong"},
            {"text": "8И31", "url": "/right"}
        ]

        self.assertEqual(
            select_group_result(results, "8И31"),
            {"text": "8И31", "url": "/right"}
        )

    def test_select_group_result_returns_none_without_exact_match(self) -> None:
        results = [
            {"text": "8И310", "url": "/wrong"},
            {"text": "8И32", "url": "/other"}
        ]

        self.assertIsNone(
            select_group_result(
                results,
                "8И31",
                status_callback=lambda _message: None
            )
        )

    def test_search_group_uses_exact_match_from_response(self) -> None:
        response = FakeResponse({
            "result": [
                {"text": "8И310", "url": "/wrong"},
                {"text": "8И31", "url": "/right"}
            ]
        })

        with patch(
            "app.group_search.make_request",
            return_value=response
        ):
            result = search_group(
                "8i31",
                status_callback=lambda _message: None
            )

        self.assertEqual(result["url"], "/right")


if __name__ == "__main__":
    unittest.main()