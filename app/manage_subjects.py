import json

from config import SUBJECTS_FILE


def load_subjects() -> list[dict]:
    with open(
        SUBJECTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_subjects(subjects: list[dict]) -> None:
    with open(
        SUBJECTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            subjects,
            file,
            ensure_ascii=False,
            indent=2
        )


def set_subject_enabled(
    subjects: list[dict],
    title: str,
    enabled: bool
) -> bool:
    for subject in subjects:
        if subject["title"] == title:
            subject["enabled"] = enabled
            return True

    return False


def set_all_subjects_enabled(
    subjects: list[dict],
    enabled: bool
) -> None:
    for subject in subjects:
        subject["enabled"] = enabled


def toggle_subjects_by_indexes(
    subjects: list[dict],
    indexes: list[int]
) -> None:
    for index in indexes:
        subject = subjects[index - 1]
        subject["enabled"] = not subject.get("enabled", True)


def show_subjects(subjects: list[dict]) -> None:
    print("\nПредметы:\n")

    for index, subject in enumerate(subjects, start=1):
        status = "ON " if subject.get("enabled", True) else "OFF"

        print(
            f"{index:2}. [{status}] {subject['title']}"
        )


def parse_indexes(user_input: str, max_index: int) -> list[int]:
    parts = user_input.replace(",", " ").split()

    indexes = []

    for part in parts:
        if not part.isdigit():
            continue

        number = int(part)

        if 1 <= number <= max_index:
            indexes.append(number)

    return sorted(set(indexes))


def main():
    subjects = load_subjects()

    while True:
        show_subjects(subjects)

        print("\nКоманды:")
        print("номер(а) — переключить предметы, например: 1 3 5")
        print("all — включить все")
        print("none — выключить все")
        print("save — сохранить и выйти")
        print("exit — выйти без сохранения")

        user_input = input("\nВвод: ").strip().lower()

        if user_input == "save":
            save_subjects(subjects)
            print("\nsubjects.json сохранён")
            break

        if user_input == "exit":
            print("\nВыход без сохранения")
            break

        if user_input == "all":
            set_all_subjects_enabled(subjects, True)

            continue

        if user_input == "none":
            set_all_subjects_enabled(subjects, False)

            continue

        indexes = parse_indexes(
            user_input,
            len(subjects)
        )

        toggle_subjects_by_indexes(subjects, indexes)


if __name__ == "__main__":
    main()
