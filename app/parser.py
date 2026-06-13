from datetime import date, datetime
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app_logging import StatusCallback, emit
from config import CONFIG
from group_search import resolve_group_id


STUDY_YEAR = CONFIG["study_year"]
STUDY_YEAR_START = date(STUDY_YEAR, 9, 1)


class ScheduleParseError(Exception):
    pass


def get_current_study_week(today: date) -> int:
    delta_days = (today - STUDY_YEAR_START).days

    if delta_days < 0:
        raise ValueError("Текущая дата раньше начала учебного года")

    return delta_days // 7 + 1


def build_schedule_url(group_id: str, study_year: int, week: int) -> str:
    return f"https://ro-rasp.tpu.ru/gruppa_{group_id}/{study_year}/{week}/view.html"


def fetch_rendered_html(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto(
            url,
            wait_until="networkidle",
            timeout=60000
        )

        html = page.content()

        browser.close()

    return html


def fetch_rendered_html_many(
    urls: list[str],
    status_callback: StatusCallback | None = None
) -> dict[str, str]:
    result = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url in urls:
            emit(f"Загружаю: {url}", status_callback)

            page.goto(
                url,
                wait_until="networkidle",
                timeout=60000
            )

            result[url] = page.content()

        browser.close()

    return result


def get_schedule_table(soup: BeautifulSoup):
    table = soup.select_one("#raspisanie-table")

    if table is None:
        raise ScheduleParseError(
            "Не найдена таблица расписания #raspisanie-table. "
            "Возможно, сайт ТПУ изменил разметку или вернул страницу ошибки."
        )

    return table


def extract_dates(table) -> list[str]:
    dates = []

    header_cells = table.select(
        "thead th"
    )

    for cell in header_cells:
        text = cell.get_text(" ", strip=True)

        if "." not in text:
            continue

        raw_date = text.split()[0]

        try:
            parsed_date = datetime.strptime(
                raw_date,
                "%d.%m.%y"
            ).date()

            dates.append(parsed_date.isoformat())

        except ValueError:
            pass

    if not dates:
        raise ScheduleParseError(
            "Не удалось найти даты в заголовке таблицы расписания."
        )

    return dates


def extract_date_from_cell(cell) -> str | None:
    links = cell.select("a[href*='date=']")

    for link in links:
        href = link.get("href", "")

        parsed_url = urlparse(href)

        query = parse_qs(parsed_url.query)

        if "date" in query:
            raw_date = query["date"][0]

            try:
                parsed_date = datetime.strptime(
                    raw_date,
                    "%d.%m.%Y"
                ).date()

            except ValueError:
                continue

            return parsed_date.isoformat()

    return None


def extract_time(row) -> tuple[str, str]:
    time_cell = row.select_one("td")

    if time_cell is None or not time_cell.contents:
        raise ScheduleParseError(
            "В строке расписания не найдена ячейка времени."
        )

    end_time_cell = time_cell.select_one(".text-muted")

    if end_time_cell is None:
        raise ScheduleParseError(
            "В строке расписания не найдено время окончания занятия."
        )

    start_time = (
        time_cell.contents[0]
        .strip()
    )

    if not start_time:
        raise ScheduleParseError(
            "В строке расписания пустое время начала занятия."
        )

    end_time = (
        end_time_cell.get_text(strip=True)
    )

    return start_time, end_time


def split_cell_into_lesson_blocks(cell):
    blocks = []

    current = []

    for child in cell.children:
        if getattr(child, "name", None) == "hr":
            if current:
                blocks.append(current)
                current = []

        else:
            current.append(child)

    if current:
        blocks.append(current)

    result = []

    for block_children in blocks:
        fake = BeautifulSoup(
            "<div></div>",
            "html.parser"
        )

        wrapper = fake.div

        for child in block_children:
            wrapper.append(child)

        result.append(wrapper)

    return result


def parse_lesson_block(block) -> dict | None:
    subject_span = block.select_one("span[title]")

    full_title = ""

    if subject_span:
        full_title = subject_span.get("title", "").strip()

    text = block.get_text(
        " ",
        strip=True
    )

    if not text:
        return None

    parts = text.split()

    lesson_type = ""

    type_markers = [
        "ЛК",
        "ЛБ",
        "ПР",
        "СМ",
        "КС",
        "Э",
        "ЗЧ"
    ]

    type_index = None

    for i, part in enumerate(parts):
        clean_part = (
            part
            .replace("(", "")
            .replace(")", "")
            .strip()
        )

        if clean_part in type_markers:
            lesson_type = clean_part
            type_index = i
            break

    if type_index is None:
        return {
            "title": full_title or text,
            "type": "",
            "teacher": "",
            "location": ""
        }

    title = full_title or (
        " ".join(parts[:type_index])
        .replace("(", "")
        .strip()
    )

    rest = parts[type_index + 1:]

    rest = [
        p for p in rest
        if p not in ["(", ")"]
    ]

    rest_text = " ".join(rest)

    location = ""
    teacher = rest_text

    if "к." in rest_text:
        teacher_part, location_part = rest_text.split(
            "к.",
            1
        )

        teacher = teacher_part.strip()

        location = (
            "к. " +
            location_part.strip()
        )

    if not title and teacher and not location:
        title = teacher
        teacher = ""

    location = (
        location
        .replace(" ,", ",")
        .replace("  ", " ")
        .strip()
    )

    return {
        "title": title,
        "type": lesson_type,
        "teacher": teacher,
        "location": location
    }


def parse_schedule(
    html: str,
    status_callback: StatusCallback | None = None
) -> list[dict]:
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    table = get_schedule_table(soup)
    dates = extract_dates(table)

    lessons = []

    rows = table.select("tbody tr")

    if not rows:
        raise ScheduleParseError(
            "В таблице расписания не найдены строки занятий."
        )

    for row in rows:
        try:
            start_time, end_time = extract_time(row)

        except ScheduleParseError as error:
            emit(
                f"Пропущена строка расписания: {error}",
                status_callback
            )
            continue

        cells = row.find_all(
            "td",
            recursive=False
        )

        for cell_index, cell in enumerate(cells[1:], start=1):
            day_index = cell_index - 1

            if day_index >= len(dates):
                continue

            classes = cell.get("class", [])

            if "cell" not in classes:
                continue

            if not cell.get_text(strip=True):
                continue

            cell_date = extract_date_from_cell(cell)

            blocks = split_cell_into_lesson_blocks(cell)

            for block in blocks:
                try:
                    lesson_data = parse_lesson_block(block)

                except Exception as error:
                    emit(
                        "Пропущен блок занятия: "
                        f"{error}",
                        status_callback
                    )
                    continue

                if lesson_data is None:
                    continue

                lesson = {
                    "date": cell_date or dates[day_index],
                    "start": start_time,
                    "end": end_time,
                    **lesson_data
                }

                lessons.append(lesson)

    return lessons


def main():
    today = date.today()

    week = get_current_study_week(today)
    group_name = CONFIG["group_name"]
    group_id = resolve_group_id(group_name)

    if not group_id:
        raise ValueError(
            f"Не удалось найти группу: {group_name}"
        )

    url = build_schedule_url(
        group_id,
        STUDY_YEAR,
        week
    )

    print("URL:", url)

    html = fetch_rendered_html(url)



    lessons = parse_schedule(html)

    print(f"\nНайдено занятий: {len(lessons)}\n")

    for lesson in lessons:
        print(lesson)

    subjects = sorted(
        set(
            lesson["title"]
            for lesson in lessons
        )
    )

    print("\nУникальные предметы:\n")

    for index, subject in enumerate(
        subjects,
        start=1
    ):
        print(f"{index}. {subject}")


if __name__ == "__main__":
    main()
