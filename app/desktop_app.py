import threading
import traceback
from collections.abc import Callable

try:
    import customtkinter as ctk
    from PIL import Image

except ImportError as error:
    raise SystemExit(
        "Не установлены зависимости GUI. Выполните: "
        ".\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
    ) from error

from .app_actions import (
    delete_calendar,
    full_sync,
    load_subjects,
    save_subjects,
    sync_calendar,
    update_schedule
)
from .config import AVATAR_FILE, CONFIG
from .manage_subjects import set_all_subjects_enabled


Action = Callable[[Callable[[str], None]], dict | bool]


class DesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TPU Calendar Sync")
        self.geometry("920x620")
        self.minsize(760, 520)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.buttons: list[ctk.CTkButton] = []
        self.subjects: list[dict] = []
        self.subject_vars: list[ctk.BooleanVar] = []

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(2, weight=1)

        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self) -> None:
        if AVATAR_FILE.exists():
            avatar = ctk.CTkImage(
                light_image=Image.open(AVATAR_FILE),
                dark_image=Image.open(AVATAR_FILE),
                size=(92, 92)
            )

            avatar_label = ctk.CTkLabel(
                self.sidebar,
                text="",
                image=avatar
            )
            avatar_label.grid(row=0, column=0, padx=18, pady=(22, 8), sticky="ew")
            self.avatar_image = avatar

        title = ctk.CTkLabel(
            self.sidebar,
            text="TPU Calendar Sync",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=1, column=0, padx=18, pady=(0, 8), sticky="ew")

        group_text = (
            f"Группа: {CONFIG['group_name']}\n"
            f"Год: {CONFIG['study_year']}\n"
            f"Недель: {CONFIG['weeks_ahead']}"
        )

        group_label = ctk.CTkLabel(
            self.sidebar,
            text=group_text,
            justify="left"
        )
        group_label.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="w")

        self._add_action_button(
            row=3,
            text="Обновить расписание",
            command=lambda: self.run_action(
                "Обновление расписания",
                update_schedule
            )
        )

        self._add_action_button(
            row=4,
            text="Синхронизировать календарь",
            command=lambda: self.run_action(
                "Синхронизация календаря",
                sync_calendar
            )
        )

        self._add_action_button(
            row=5,
            text="Полная синхронизация",
            command=lambda: self.run_action(
                "Полная синхронизация",
                full_sync
            )
        )

        self._add_action_button(
            row=6,
            text="Удалить календарь TPU",
            command=self.confirm_delete_calendar,
            color="#8f2d2d",
            hover_color="#a53636"
        )

        clear_button = ctk.CTkButton(
            self.sidebar,
            text="Очистить лог",
            command=self.clear_log
        )
        clear_button.grid(row=8, column=0, padx=18, pady=(18, 8), sticky="ew")

        exit_button = ctk.CTkButton(
            self.sidebar,
            text="Закрыть",
            command=self.destroy
        )
        exit_button.grid(row=10, column=0, padx=18, pady=18, sticky="ew")

    def _add_action_button(
        self,
        row: int,
        text: str,
        command: Callable[[], None],
        color: str | None = None,
        hover_color: str | None = None
    ) -> None:
        button = ctk.CTkButton(
            self.sidebar,
            text=text,
            command=command,
            fg_color=color,
            hover_color=hover_color
        )
        button.grid(row=row, column=0, padx=18, pady=7, sticky="ew")
        self.buttons.append(button)

    def _build_content(self) -> None:
        self.status_label = ctk.CTkLabel(
            self.content,
            text="Готово к работе",
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=(18, 8), sticky="ew")

        self.tabs = ctk.CTkTabview(self.content)
        self.tabs.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

        self.log_tab = self.tabs.add("Журнал")
        self.subjects_tab = self.tabs.add("Предметы")

        self.log_tab.grid_columnconfigure(0, weight=1)
        self.log_tab.grid_rowconfigure(0, weight=1)

        self.subjects_tab.grid_columnconfigure(0, weight=1)
        self.subjects_tab.grid_rowconfigure(1, weight=1)

        self.log_box = ctk.CTkTextbox(
            self.log_tab,
            wrap="word"
        )
        self.log_box.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.log_box.insert("end", "Приложение запущено.\n")
        self.log_box.configure(state="disabled")

        self._build_subjects_tab()
        self.reload_subjects()

    def _build_subjects_tab(self) -> None:
        toolbar = ctk.CTkFrame(self.subjects_tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        toolbar.grid_columnconfigure(3, weight=1)

        enable_all = ctk.CTkButton(
            toolbar,
            text="Включить все",
            width=130,
            command=lambda: self.set_all_subjects(True)
        )
        enable_all.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.buttons.append(enable_all)

        disable_all = ctk.CTkButton(
            toolbar,
            text="Выключить все",
            width=130,
            command=lambda: self.set_all_subjects(False)
        )
        disable_all.grid(row=0, column=1, padx=(0, 8), sticky="w")
        self.buttons.append(disable_all)

        reload_button = ctk.CTkButton(
            toolbar,
            text="Обновить список",
            width=140,
            command=self.reload_subjects
        )
        reload_button.grid(row=0, column=2, padx=(0, 8), sticky="w")
        self.buttons.append(reload_button)

        save_button = ctk.CTkButton(
            toolbar,
            text="Сохранить",
            width=120,
            command=self.save_subjects_from_ui
        )
        save_button.grid(row=0, column=4, sticky="e")
        self.buttons.append(save_button)

        self.subjects_frame = ctk.CTkScrollableFrame(self.subjects_tab)
        self.subjects_frame.grid(row=1, column=0, sticky="nsew")
        self.subjects_frame.grid_columnconfigure(0, weight=1)

        self.subjects_hint = ctk.CTkLabel(
            self.subjects_tab,
            text="",
            anchor="w"
        )
        self.subjects_hint.grid(row=2, column=0, pady=(10, 0), sticky="ew")

    def confirm_delete_calendar(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Удалить календарь")
        dialog.geometry("420x170")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        label = ctk.CTkLabel(
            dialog,
            text="Удалить календарь TPU Schedule из Google Calendar?",
            wraplength=360
        )
        label.pack(padx=24, pady=(24, 16))

        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.pack(padx=24, pady=(0, 24), fill="x")
        actions.grid_columnconfigure((0, 1), weight=1)

        cancel = ctk.CTkButton(
            actions,
            text="Отмена",
            command=dialog.destroy
        )
        cancel.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        confirm = ctk.CTkButton(
            actions,
            text="Удалить",
            fg_color="#8f2d2d",
            hover_color="#a53636",
            command=lambda: self._delete_after_confirm(dialog)
        )
        confirm.grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _delete_after_confirm(self, dialog: ctk.CTkToplevel) -> None:
        dialog.destroy()
        self.run_action("Удаление календаря", delete_calendar)

    def run_action(self, title: str, action: Action) -> None:
        self.set_busy(True)
        self.write_log(f"\n{title}")
        self.status_label.configure(text=f"Выполняется: {title}")

        thread = threading.Thread(
            target=self._run_worker,
            args=(title, action),
            daemon=True
        )
        thread.start()

    def _run_worker(self, title: str, action: Action) -> None:
        try:
            result = action(self.write_log_threadsafe)
            self.after(
                0,
                lambda: self._finish_action(title, result)
            )

        except Exception:
            error_text = traceback.format_exc()
            self.after(
                0,
                lambda: self._fail_action(title, error_text)
            )

    def _finish_action(self, title: str, result: dict | bool) -> None:
        self.write_log(f"{title}: завершено")

        if isinstance(result, dict):
            self.write_summary(result)

            if "subjects_count" in result or "schedule" in result:
                self.reload_subjects()

        self.status_label.configure(text="Готово к работе")
        self.set_busy(False)

    def _fail_action(self, title: str, error_text: str) -> None:
        self.write_log(f"{title}: ошибка")
        self.write_log(error_text)
        self.status_label.configure(text="Ошибка выполнения")
        self.set_busy(False)

    def write_summary(self, result: dict) -> None:
        if "lessons_count" in result:
            self.write_log(
                f"Итог: занятий {result['lessons_count']}, "
                f"предметов {result['subjects_count']}"
            )
            return

        if "created_count" in result:
            self.write_log(
                f"Итог: создано {result['created_count']}, "
                f"обновлено {result['updated_count']}, "
                f"удалено {result['deleted_count']}"
            )
            return

        if "schedule" in result and "calendar" in result:
            schedule = result["schedule"]
            calendar = result["calendar"]
            self.write_log(
                f"Итог: занятий {schedule['lessons_count']}, "
                f"создано {calendar['created_count']}, "
                f"обновлено {calendar['updated_count']}, "
                f"удалено {calendar['deleted_count']}"
            )

    def write_log_threadsafe(self, message: str) -> None:
        self.after(0, lambda: self.write_log(message))

    def write_log(self, message: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def reload_subjects(self) -> None:
        for child in self.subjects_frame.winfo_children():
            child.destroy()

        self.subject_vars = []

        try:
            self.subjects = load_subjects()

        except FileNotFoundError:
            self.subjects = []
            self.subjects_hint.configure(
                text="Список появится после обновления расписания."
            )
            return

        if not self.subjects:
            self.subjects_hint.configure(text="Предметы не найдены.")
            return

        enabled_count = 0

        for row, subject in enumerate(self.subjects):
            enabled = subject.get("enabled", True)

            if enabled:
                enabled_count += 1

            variable = ctk.BooleanVar(value=enabled)
            self.subject_vars.append(variable)

            checkbox = ctk.CTkCheckBox(
                self.subjects_frame,
                text=subject["title"],
                variable=variable
            )
            checkbox.grid(row=row, column=0, padx=8, pady=5, sticky="w")

        self.subjects_hint.configure(
            text=(
                f"Предметов: {len(self.subjects)}. "
                f"Включено: {enabled_count}."
            )
        )

    def set_all_subjects(self, enabled: bool) -> None:
        set_all_subjects_enabled(self.subjects, enabled)

        for variable in self.subject_vars:
            variable.set(enabled)

        self.subjects_hint.configure(
            text=(
                f"Предметов: {len(self.subjects)}. "
                f"Включено: {len(self.subjects) if enabled else 0}."
            )
        )

    def save_subjects_from_ui(self) -> None:
        if not self.subjects:
            self.write_log("Нет предметов для сохранения.")
            return

        enabled_count = 0

        for subject, variable in zip(
            self.subjects,
            self.subject_vars,
            strict=False
        ):
            enabled = bool(variable.get())
            subject["enabled"] = enabled

            if enabled:
                enabled_count += 1

        save_subjects(self.subjects)
        self.subjects_hint.configure(
            text=(
                f"Предметов: {len(self.subjects)}. "
                f"Включено: {enabled_count}."
            )
        )
        self.write_log("subjects.json сохранён.")

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"

        for button in self.buttons:
            button.configure(state=state)


def main() -> None:
    app = DesktopApp()
    app.mainloop()
