import re
import time

import requests

from .app_logging import StatusCallback, emit


BASE_URL = "https://ro-rasp.tpu.ru"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0"
    )
}

GROUP_NAME_FIELDS = (
    "name",
    "title",
    "text",
    "label",
    "value"
)


def normalize_group_name(group_name: str) -> str:
    normalized = group_name.strip().upper()

    return normalized.replace("I", "И")


def clean_result_text(value: str) -> str:
    return re.sub(
        r"<[^>]+>",
        " ",
        value
    )


def result_texts(result: dict) -> list[str]:
    texts = []

    for field in GROUP_NAME_FIELDS:
        value = result.get(field)

        if isinstance(value, str) and value.strip():
            texts.append(clean_result_text(value))

    return texts


def result_matches_group(result: dict, group_name: str) -> bool:
    target = normalize_group_name(group_name)

    for text in result_texts(result):
        normalized = normalize_group_name(text)

        if normalized == target:
            return True

        tokens = [
            token
            for token in re.split(r"[\s,;()\[\]{}]+", normalized)
            if token
        ]

        if target in tokens:
            return True

    return False


def select_group_result(
    results: list[dict],
    group_name: str,
    status_callback: StatusCallback | None = None
) -> dict | None:
    matches = [
        result
        for result in results
        if result_matches_group(result, group_name)
    ]

    if not matches:
        emit(
            f"Точного совпадения для группы {group_name} не найдено.",
            status_callback
        )
        return None

    if len(matches) > 1:
        emit(
            f"Найдено несколько точных совпадений для группы {group_name}. "
            "Использую первое.",
            status_callback
        )

    return matches[0]


def make_request(
    url: str,
    status_callback: StatusCallback | None = None,
    **kwargs
):
    last_error = None

    for attempt in range(3):
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=15,
                **kwargs
            )

            response.raise_for_status()

            return response

        except Exception as error:
            last_error = error

            emit(
                f"Ошибка сети "
                f"(попытка {attempt + 1}/3): "
                f"{error}",
                status_callback
            )

            time.sleep(2)

    raise last_error


def search_group(
    group_name: str,
    status_callback: StatusCallback | None = None
) -> dict | None:
    group_name = normalize_group_name(group_name)

    response = make_request(
        f"{BASE_URL}/select/search/main.html",
        params={
            "q": group_name,
            "page_limit": 25,
            "page": 1
        },
        status_callback=status_callback
    )

    data = response.json()

    results = data.get(
        "result",
        []
    )

    if not results:
        return None

    return select_group_result(
        results,
        group_name,
        status_callback=status_callback
    )


def resolve_group_id(
    group_name: str,
    status_callback: StatusCallback | None = None
) -> str | None:
    group_name = normalize_group_name(group_name)

    group = search_group(
        group_name,
        status_callback=status_callback
    )

    if not group:
        return None

    redirect_url = (
        BASE_URL +
        group["url"]
    )

    response = make_request(
        redirect_url,
        allow_redirects=True,
        status_callback=status_callback
    )

    final_url = response.url

    match = re.search(
        r"gruppa_(\d+)",
        final_url
    )

    if not match:
        return None

    return match.group(1)
