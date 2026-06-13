if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(
        0,
        str(Path(__file__).resolve().parent.parent)
    )
    __package__ = "app"

from .app_actions import (
    delete_calendar,
    full_sync,
    sync_calendar,
    update_schedule
)
from .manage_subjects import main as manage_subjects_menu


def show_menu():
    print("\nTPU Calendar Sync")
    print("1. Обновить расписание из TPU")
    print("2. Управлять предметами")
    print("3. Синхронизировать Google Calendar")
    print("4. Полная синхронизация")
    print("5. Удалить календарь TPU")
    print("0. Выход")


def main():
    while True:
        show_menu()

        choice = input("\nВыбор: ").strip()

        if choice == "1":
            result = update_schedule()

            print("\nГотово")
            print("Занятий сохранено:", result["lessons_count"])
            print("Предметов найдено:", result["subjects_count"])

        elif choice == "2":
            manage_subjects_menu()

        elif choice == "3":
            result = sync_calendar()

            print("\nГотово")
            print("Создано:", result["created_count"])
            print("Обновлено:", result["updated_count"])
            print("Удалено:", result["deleted_count"])

        elif choice == "4":
            result = full_sync()
            calendar_result = result["calendar"]

            print("\nГотово")
            print(
                "Занятий сохранено:",
                result["schedule"]["lessons_count"]
            )
            print("Создано:", calendar_result["created_count"])
            print("Обновлено:", calendar_result["updated_count"])
            print("Удалено:", calendar_result["deleted_count"])

        elif choice == "5":
            delete_calendar()

        elif choice == "0":
            print("Выход")
            break

        else:
            print("Неизвестная команда")


if __name__ == "__main__":
    main()
