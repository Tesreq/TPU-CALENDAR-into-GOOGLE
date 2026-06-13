import re
import time

import requests

from app_logging import StatusCallback, emit


BASE_URL = "https://ro-rasp.tpu.ru"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0"
    )
}


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

    return results[0]


def resolve_group_id(
    group_name: str,
    status_callback: StatusCallback | None = None
) -> str | None:

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
