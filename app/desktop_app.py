import threading
import traceback
from tkinter import filedialog
from collections.abc import Callable
from datetime import date

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
    import_google_credentials,
    login_google_account,
    load_subjects,
    logout_google_account,
    save_subjects,
    sync_calendar,
    update_schedule
)
from .calendar_api import has_saved_google_login
from .config import (
    AVATAR_FILE,
    CONFIG,
    CREDENTIALS_FILE,
    save_config
)
from .environment_check import check_environment
from .group_search import normalize_group_name, resolve_group_id
from .manage_subjects import set_all_subjects_enabled
from .parser import get_current_study_week, get_current_study_year


Action = Callable[[Callable[[str], None]], dict | bool]

BLUE = "#1a73e8"
GREEN = "#34a853"
RED = "#ea4335"
WARNING = "#f9ab00"
TEXT = "#202124"
MUTED = "#5f6368"
BORDER = "#d9e2ef"
SURFACE = "#ffffff"
APP_BG = "#f8fafd"
APP_MIN_WIDTH = 1180
APP_MIN_HEIGHT = 900
LOG_MIN_HEIGHT = 620


class DesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TPU Calendar Sync")
        self.geometry(f"1180x{APP_MIN_HEIGHT}")
        self.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)
        self.configure(fg_color=APP_BG)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.buttons: list[ctk.CTkButton] = []
        self.subjects: list[dict] = []
        self.subject_vars: dict[str, ctk.BooleanVar] = {}

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self,
            width=265,
            corner_radius=0,
            fg_color="#f5f9ff"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.content = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=APP_BG
        )
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(4, weight=1)

        self._build_sidebar()
        self._build_content()
        self.refresh_status_panel()

    def _build_sidebar(self) -> None:
        app_title = ctk.CTkLabel(
            self.sidebar,
            text="TPU Calendar Sync",
            text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        app_title.grid(row=0, column=0, padx=20, pady=(18, 14), sticky="ew")

        card = ctk.CTkFrame(
            self.sidebar,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8
        )
        card.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        if AVATAR_FILE.exists():
            avatar = ctk.CTkImage(
                light_image=Image.open(AVATAR_FILE),
                dark_image=Image.open(AVATAR_FILE),
                size=(82, 82)
            )

            avatar_label = ctk.CTkLabel(card, text="", image=avatar)
            avatar_label.grid(row=0, column=0, padx=18, pady=(20, 8))
            self.avatar_image = avatar

        title = ctk.CTkLabel(
            card,
            text="TPU Calendar Sync",
            text_color=TEXT,
            font=ctk.CTkFont(size=19, weight="bold")
        )
        title.grid(row=1, column=0, padx=18, pady=(4, 0))

        version = ctk.CTkLabel(
            card,
            text="v1.2.0",
            text_color=MUTED,
            font=ctk.CTkFont(size=12)
        )
        version.grid(row=2, column=0, padx=18, pady=(2, 18))

        self.sidebar_info = ctk.CTkLabel(
            card,
            text="",
            text_color=TEXT,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=14)
        )
        self.sidebar_info.grid(row=3, column=0, padx=22, pady=(0, 18), sticky="ew")

        divider = ctk.CTkFrame(card, height=1, fg_color=BORDER)
        divider.grid(row=4, column=0, padx=18, pady=(0, 14), sticky="ew")

        self._add_action_button(
            card,
            row=5,
            text="Синхронизировать",
            command=lambda: self.run_google_required_action(
                "Синхронизация",
                full_sync
            ),
            primary=True
        )

        spacer = ctk.CTkFrame(card, height=26, fg_color="transparent")
        spacer.grid(row=6, column=0, sticky="ew")

        exit_button = self._make_button(
            card,
            text="Выход из приложения",
            command=self.destroy,
            outline=True
        )
        self._style_sidebar_button(exit_button)
        exit_button.grid(row=7, column=0, padx=20, pady=(0, 18), sticky="ew")

        footer = ctk.CTkLabel(
            card,
            text="© 2025 TPU Calendar Sync\nСделано для студентов ТПУ",
            text_color=MUTED,
            justify="left",
            font=ctk.CTkFont(size=12)
        )
        footer.grid(row=8, column=0, padx=20, pady=(0, 16), sticky="w")

        self.refresh_sidebar_info()

    def _make_button(
        self,
        parent,
        text: str,
        command: Callable[[], None],
        primary: bool = False,
        danger: bool = False,
        outline: bool = False
    ) -> ctk.CTkButton:
        if primary:
            return ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color=BLUE,
                hover_color="#155ec2",
                text_color="white",
                height=38,
                corner_radius=6
            )

        if danger:
            return ctk.CTkButton(
                parent,
                text=text,
                command=command,
                fg_color="#fff8f8",
                hover_color="#ffecec",
                border_width=1,
                border_color="#ffb3b3",
                text_color=RED,
                height=38,
                corner_radius=6
            )

        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=SURFACE if outline else "#eef4ff",
            hover_color="#edf4ff",
            border_width=1 if outline else 0,
            border_color="#cbd7ea",
            text_color=BLUE,
            height=38,
            corner_radius=6
        )

    def _style_sidebar_button(
        self,
        button: ctk.CTkButton,
        danger: bool = False
    ) -> None:
        text_color = RED if danger else BLUE
        border_color = "#ffb3b3" if danger else "#cbd7ea"
        button.sidebar_danger = danger

        button.configure(
            fg_color=SURFACE,
            hover_color=BLUE,
            border_width=1,
            border_color=border_color,
            text_color=text_color
        )

        def on_enter(_event) -> None:
            if button.cget("state") == "disabled":
                return

            button.configure(
                fg_color=BLUE,
                border_color=BLUE,
                text_color="white"
            )

        def on_leave(_event) -> None:
            button.configure(
                fg_color=SURFACE,
                border_color=border_color,
                text_color=text_color
            )

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)

        for child in button.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

    def _add_action_button(
        self,
        parent,
        row: int,
        text: str,
        command: Callable[[], None],
        primary: bool = False,
        danger: bool = False,
        outline: bool = False
    ) -> None:
        button = self._make_button(
            parent,
            text=text,
            command=command,
            primary=primary,
            danger=danger,
            outline=outline
        )
        self._style_sidebar_button(button, danger=danger)
        button.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
        self.buttons.append(button)

    def _build_content(self) -> None:
        self.status_panel = ctk.CTkFrame(
            self.content,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8
        )
        self.status_panel.grid(row=0, column=0, padx=24, pady=(22, 14), sticky="ew")
        self.status_panel.grid_propagate(False)
        self.status_panel.configure(height=82)
        self.status_panel.grid_columnconfigure((0, 1), weight=1, uniform="status")

        self.tpu_status, self.tpu_status_marker = self._build_status_item(
            0,
            "Расписание",
            "Не загружено"
        )
        self.account_status, self.account_status_marker = self._build_status_item(
            1,
            "Google",
            "Вход в Google не выполнен"
        )

        self.status_label = ctk.CTkLabel(
            self.content,
            text="Готово к работе",
            text_color=MUTED,
            anchor="w"
        )
        self.status_label.grid(row=1, column=0, padx=26, pady=(0, 4), sticky="ew")

        self.tab_nav = ctk.CTkFrame(
            self.content,
            fg_color=APP_BG
        )
        self.tab_nav.grid(row=2, column=0, padx=24, pady=(12, 0), sticky="ew")
        self.tab_nav.grid_columnconfigure(4, weight=1)

        self.tab_buttons: dict[str, ctk.CTkButton] = {}
        self.tab_underlines: dict[str, ctk.CTkFrame] = {}

        self._add_tab_button("log", "Журнал", 0)
        self._add_tab_button("subjects", "Предметы", 1)
        self._add_tab_button("settings", "Настройки", 2)
        self._add_tab_button("extra", "Дополнительно", 3)

        nav_line = ctk.CTkFrame(
            self.content,
            height=1,
            fg_color=BORDER
        )
        nav_line.grid(row=3, column=0, padx=24, pady=(0, 14), sticky="ew")

        self.tab_container = ctk.CTkFrame(
            self.content,
            fg_color=APP_BG,
            corner_radius=0
        )
        self.tab_container.grid(row=4, column=0, padx=24, pady=(0, 22), sticky="nsew")
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)

        self.log_tab = ctk.CTkFrame(
            self.tab_container,
            fg_color=APP_BG,
            corner_radius=0
        )
        self.subjects_tab = ctk.CTkFrame(
            self.tab_container,
            fg_color=APP_BG,
            corner_radius=0
        )
        self.settings_tab = ctk.CTkFrame(
            self.tab_container,
            fg_color=APP_BG,
            corner_radius=0
        )
        self.extra_tab = ctk.CTkFrame(
            self.tab_container,
            fg_color=APP_BG,
            corner_radius=0
        )

        self.tab_frames = {
            "log": self.log_tab,
            "subjects": self.subjects_tab,
            "settings": self.settings_tab,
            "extra": self.extra_tab
        }

        self._build_log_tab()
        self._build_subjects_tab()
        self._build_settings_tab()
        self._build_extra_tab()
        self.reload_subjects()
        self.show_tab("log")

    def _add_tab_button(self, tab_id: str, text: str, column: int) -> None:
        tab = ctk.CTkFrame(
            self.tab_nav,
            fg_color="transparent"
        )
        tab.grid(row=0, column=column, padx=(0, 28), sticky="w")

        button = ctk.CTkButton(
            tab,
            text=text,
            width=92,
            height=36,
            command=lambda: self.show_tab(tab_id),
            fg_color="transparent",
            hover_color="#edf4ff",
            text_color=MUTED,
            corner_radius=0,
            font=ctk.CTkFont(size=15)
        )
        button.grid(row=0, column=0, sticky="ew")

        underline = ctk.CTkFrame(
            tab,
            height=2,
            fg_color=APP_BG
        )
        underline.grid(row=1, column=0, sticky="ew")

        self.tab_buttons[tab_id] = button
        self.tab_underlines[tab_id] = underline

    def show_tab(self, tab_id: str) -> None:
        for frame in self.tab_frames.values():
            frame.grid_forget()

        self.tab_frames[tab_id].grid(row=0, column=0, sticky="nsew")

        for current_tab_id, button in self.tab_buttons.items():
            is_active = current_tab_id == tab_id

            button.configure(
                text_color=BLUE if is_active else MUTED,
                font=ctk.CTkFont(
                    size=15,
                    weight="bold" if is_active else "normal"
                )
            )
            self.tab_underlines[current_tab_id].configure(
                fg_color=BLUE if is_active else APP_BG
            )

    def _build_status_item(
        self,
        column: int,
        title: str,
        subtitle: str
    ) -> tuple[ctk.CTkLabel, ctk.CTkLabel]:
        item = ctk.CTkFrame(
            self.status_panel,
            fg_color="transparent"
        )
        item.grid(row=0, column=column, padx=18, pady=16, sticky="ew")
        item.grid_columnconfigure(1, weight=1)

        marker = ctk.CTkLabel(
            item,
            text="●",
            text_color=GREEN,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        marker.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="w")

        title_label = ctk.CTkLabel(
            item,
            text=title,
            text_color=TEXT,
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=1, sticky="ew")

        subtitle_label = ctk.CTkLabel(
            item,
            text=subtitle,
            text_color=MUTED,
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        subtitle_label.grid(row=1, column=1, sticky="ew")

        return subtitle_label, marker

    def _build_log_tab(self) -> None:
        self.log_tab.grid_columnconfigure(0, weight=1)
        self.log_tab.grid_rowconfigure(2, weight=1)

        self._build_first_run_panel()

        summary = ctk.CTkFrame(
            self.log_tab,
            fg_color="transparent",
            corner_radius=0
        )
        summary.grid(row=1, column=0, sticky="ew", pady=(4, 12))
        summary.grid_columnconfigure(1, weight=1)

        ready_title = ctk.CTkLabel(
            summary,
            text="Журнал",
            text_color=TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        ready_title.grid(row=0, column=0, sticky="w")

        ready_subtitle = ctk.CTkLabel(
            summary,
            text="Готово к работе",
            text_color=MUTED,
            anchor="w"
        )
        ready_subtitle.grid(row=0, column=1, padx=(14, 12), sticky="w")

        clear_button = self._make_button(
            summary,
            text="Очистить",
            command=self.clear_log,
            outline=True
        )
        clear_button.configure(width=112)
        clear_button.grid(row=0, column=2, sticky="e")
        self.buttons.append(clear_button)

        self.log_box = ctk.CTkTextbox(
            self.log_tab,
            wrap="word",
            height=LOG_MIN_HEIGHT,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8,
            text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.log_box.grid(row=2, column=0, sticky="nsew")
        self.log_box.insert("end", "Приложение запущено.\n")
        self.log_box.configure(state="disabled")

    def _build_first_run_panel(self) -> None:
        self.first_run_panel = ctk.CTkFrame(
            self.log_tab,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8
        )
        self.first_run_panel.grid(row=0, column=0, sticky="ew", pady=(8, 14))
        self.first_run_panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self.first_run_panel,
            text="Первый запуск",
            text_color=TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        title.grid(row=0, column=0, padx=18, pady=(16, 4), sticky="ew")

        self.first_run_status = ctk.CTkLabel(
            self.first_run_panel,
            text="",
            text_color=MUTED,
            justify="left",
            anchor="w"
        )
        self.first_run_status.grid(row=1, column=0, padx=18, pady=(0, 12), sticky="ew")

        actions = ctk.CTkFrame(self.first_run_panel, fg_color="transparent")
        actions.grid(row=2, column=0, padx=18, pady=(0, 16), sticky="ew")
        actions.grid_columnconfigure(3, weight=1)
        settings_button = self._make_button(
            actions,
            text="Открыть настройки",
            command=lambda: self.show_tab("settings"),
            outline=True
        )
        settings_button.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.buttons.append(settings_button)

        google_button = self._make_button(
            actions,
            text="Войти в Google",
            command=lambda: (
                self.show_tab("extra"),
                self.run_google_auth_action()
            ),
            outline=True
        )
        google_button.grid(row=0, column=1, padx=(0, 8), sticky="w")
        self.buttons.append(google_button)

        credentials_button = self._make_button(
            actions,
            text="Выбрать credentials.json",
            command=self.choose_google_credentials,
            outline=True
        )
        credentials_button.grid(row=0, column=2, padx=(0, 8), sticky="w")
        self.buttons.append(credentials_button)

    def _build_subjects_tab(self) -> None:
        self.subjects_tab.grid_columnconfigure(0, weight=1)
        self.subjects_tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self.subjects_tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, pady=(8, 12), sticky="ew")
        toolbar.grid_columnconfigure(3, weight=1)

        enable_all = self._make_button(
            toolbar,
            text="Включить все",
            command=lambda: self.set_all_subjects(True),
            primary=True
        )
        enable_all.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.buttons.append(enable_all)

        disable_all = self._make_button(
            toolbar,
            text="Выключить все",
            command=lambda: self.set_all_subjects(False),
            outline=True
        )
        disable_all.grid(row=0, column=1, padx=(0, 8), sticky="w")
        self.buttons.append(disable_all)

        reload_button = self._make_button(
            toolbar,
            text="Обновить список",
            command=self.reload_subjects,
            outline=True
        )
        reload_button.grid(row=0, column=2, padx=(0, 12), sticky="w")
        self.buttons.append(reload_button)

        self.subject_search = ctk.CTkEntry(
            toolbar,
            placeholder_text="Поиск предмета...",
            height=38,
            border_color="#cbd7ea"
        )
        self.subject_search.grid(row=0, column=3, padx=(0, 12), sticky="ew")
        self.subject_search.bind("<KeyRelease>", lambda _event: self.render_subjects())

        save_button = self._make_button(
            toolbar,
            text="Сохранить",
            command=self.save_subjects_from_ui,
            primary=True
        )
        save_button.grid(row=0, column=4, sticky="e")
        self.buttons.append(save_button)

        subjects_card = ctk.CTkFrame(
            self.subjects_tab,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8
        )
        subjects_card.grid(row=1, column=0, sticky="nsew")
        subjects_card.grid_columnconfigure(0, weight=1)
        subjects_card.grid_rowconfigure(1, weight=1)

        self.subjects_hint = ctk.CTkLabel(
            subjects_card,
            text="",
            text_color=MUTED,
            anchor="w",
            font=ctk.CTkFont(size=13)
        )
        self.subjects_hint.grid(row=0, column=0, padx=18, pady=(14, 8), sticky="ew")

        self.subjects_frame = ctk.CTkScrollableFrame(
            subjects_card,
            fg_color=SURFACE
        )
        self.subjects_frame.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.subjects_frame.grid_columnconfigure(0, weight=1)

    def _build_extra_tab(self) -> None:
        self.extra_tab.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self.extra_tab,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8
        )
        card.grid(row=0, column=0, sticky="ew", pady=(8, 0))
        card.grid_columnconfigure((0, 1), weight=1, uniform="extra_actions")

        heading = ctk.CTkLabel(
            card,
            text="Дополнительные действия",
            text_color=TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        heading.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 12), sticky="ew")

        update_button = self._make_button(
            card,
            text="Обновить расписание",
            command=lambda: self.run_action(
                "Обновление расписания",
                update_schedule
            ),
            outline=True
        )
        update_button.grid(row=1, column=0, padx=(20, 8), pady=6, sticky="ew")
        self.buttons.append(update_button)

        calendar_button = self._make_button(
            card,
            text="Синхронизировать календарь",
            command=lambda: self.run_google_required_action(
                "Синхронизация календаря",
                sync_calendar
            ),
            outline=True
        )
        calendar_button.grid(row=1, column=1, padx=(8, 20), pady=6, sticky="ew")
        self.buttons.append(calendar_button)

        self.google_auth_button = self._make_button(
            card,
            text="Войти в Google",
            command=self.run_google_auth_action,
            outline=True
        )
        self.google_auth_button.grid(row=2, column=0, padx=(20, 8), pady=6, sticky="ew")
        self.buttons.append(self.google_auth_button)

        self.credentials_button = self._make_button(
            card,
            text="Выбрать credentials.json",
            command=self.choose_google_credentials,
            outline=True
        )
        self.credentials_button.grid(row=2, column=1, padx=(8, 20), pady=6, sticky="ew")
        self.buttons.append(self.credentials_button)

        delete_button = self._make_button(
            card,
            text="Удалить календарь TPU",
            command=self.confirm_delete_calendar,
            danger=True
        )
        delete_button.grid(row=3, column=0, columnspan=2, padx=20, pady=(6, 20), sticky="ew")
        self.buttons.append(delete_button)

    def _build_settings_tab(self) -> None:
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self.settings_tab,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8
        )
        card.grid(row=0, column=0, sticky="nsew", pady=(8, 0))
        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(2, weight=0)

        heading = ctk.CTkLabel(
            card,
            text="Основные настройки",
            text_color=TEXT,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        heading.grid(row=0, column=0, columnspan=3, padx=20, pady=(20, 10), sticky="ew")

        self.group_entry = self._add_setting_entry(
            card,
            row=1,
            title="Группа",
            description="Укажите вашу учебную группу",
            value=str(CONFIG["group_name"])
        )

        check_group_button = self._make_button(
            card,
            text="Сохранить группу",
            command=self.save_group_from_settings,
            outline=True
        )
        check_group_button.grid(row=1, column=2, padx=(0, 20), pady=16, sticky="ew")
        self.buttons.append(check_group_button)

        self.group_check_status = ctk.CTkLabel(
            card,
            text="",
            text_color=MUTED,
            anchor="w"
        )
        self.group_check_status.grid(row=2, column=1, columnspan=2, padx=20, pady=(0, 4), sticky="ew")

        self._add_setting_value(
            card,
            row=3,
            title="Учебный год",
            description="Определяется автоматически",
            value=str(get_current_study_year())
        )

        self.weeks_entry = self._add_setting_entry(
            card,
            row=4,
            title="Количество недель",
            description="Сколько недель загружать из расписания",
            value=str(CONFIG["weeks_ahead"])
        )

        self.calendar_entry = self._add_setting_entry(
            card,
            row=5,
            title="Имя календаря",
            description="Название календаря в Google Calendar",
            value=str(CONFIG["calendar_name"])
        )

        save_button = self._make_button(
            card,
            text="Сохранить настройки",
            command=self.save_settings,
            primary=True
        )
        save_button.grid(row=6, column=1, columnspan=2, padx=20, pady=(20, 20), sticky="e")
        self.buttons.append(save_button)

    def _add_setting_entry(
        self,
        parent,
        row: int,
        title: str,
        description: str,
        value: str
    ) -> ctk.CTkEntry:
        label = ctk.CTkLabel(
            parent,
            text=f"{title}\n{description}",
            text_color=TEXT,
            justify="left",
            anchor="w"
        )
        label.grid(row=row, column=0, padx=24, pady=16, sticky="ew")

        entry = ctk.CTkEntry(
            parent,
            height=38,
            border_color="#cbd7ea"
        )
        entry.insert(0, value)
        entry.grid(row=row, column=1, padx=20, pady=16, sticky="ew")

        return entry

    def _add_setting_value(
        self,
        parent,
        row: int,
        title: str,
        description: str,
        value: str
    ) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            parent,
            text=f"{title}\n{description}",
            text_color=TEXT,
            justify="left",
            anchor="w"
        )
        label.grid(row=row, column=0, padx=24, pady=16, sticky="ew")

        value_label = ctk.CTkLabel(
            parent,
            text=value,
            fg_color="#f4f7fb",
            text_color=MUTED,
            height=38,
            corner_radius=6,
            anchor="w"
        )
        value_label.grid(row=row, column=1, padx=20, pady=16, sticky="ew")

        return value_label

    def refresh_sidebar_info(self) -> None:
        group_name = CONFIG["group_name"] or "Не задана"

        try:
            current_week = get_current_study_week(
                date.today()
            )

        except ValueError:
            current_week = 0

        self.sidebar_info.configure(
            text=(
                f"Группа\n{group_name}\n\n"
                f"Неделя\n{current_week} / +{CONFIG['weeks_ahead']}"
            )
        )

    def refresh_status_panel(self) -> None:
        statuses = {
            status.key: status
            for status in check_environment()
        }

        schedule = statuses["schedule"]
        token = statuses["token"]

        self.tpu_status.configure(
            text="Загружено" if schedule.ok else schedule.message
        )
        self.tpu_status_marker.configure(
            text_color=GREEN if schedule.ok else RED
        )
        self.account_status.configure(
            text=(
                "Успешный вход в аккаунт Google"
                if token.ok
                else "Вход в Google не выполнен"
            )
        )
        self.account_status_marker.configure(
            text_color=GREEN if token.ok else RED
        )
        self.refresh_google_auth_button(token.ok)
        self.refresh_first_run_panel(token.ok)

    def refresh_first_run_panel(
        self,
        has_google_login: bool | None = None
    ) -> None:
        has_group = bool(CONFIG["group_name"].strip())
        has_credentials = CREDENTIALS_FILE.exists()

        if has_google_login is None:
            has_google_login = has_saved_google_login()

        if has_group and has_credentials and has_google_login:
            self.first_run_panel.grid_remove()
            return

        self.first_run_panel.grid()

        group_status = (
            "Группа указана"
            if has_group
            else "Укажите учебную группу в настройках"
        )
        credentials_status = (
            "credentials.json найден"
            if has_credentials
            else "Добавьте Google credentials.json"
        )
        google_status = (
            "Успешный вход в аккаунт Google"
            if has_google_login
            else "Войдите в аккаунт Google"
        )

        self.first_run_status.configure(
            text=(
                f"1. {group_status}\n"
                f"2. {credentials_status}\n"
                f"3. {google_status}"
            )
        )

    def refresh_google_auth_button(self, is_authorized: bool) -> None:
        if is_authorized:
            self.google_auth_button.configure(
                text="Выйти из Google"
            )
            self._style_sidebar_button(
                self.google_auth_button,
                danger=True
            )
            return

        self.google_auth_button.configure(
            text="Войти в Google"
        )
        self._style_sidebar_button(
            self.google_auth_button
        )

    def choose_google_credentials(self) -> None:
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Выберите Google credentials.json",
            filetypes=(
                ("JSON files", "*.json"),
                ("All files", "*.*")
            )
        )

        if not file_path:
            return

        try:
            result = import_google_credentials(file_path, self.write_log)

        except Exception as error:
            message = self.format_error_reason(
                f"{type(error).__name__}: {error}"
            )
            self.status_label.configure(text=message)
            self.write_log(f"credentials.json: ошибка - {message}")
            self.refresh_status_panel()
            return

        self.write_summary(result)
        self.refresh_status_panel()
        self.status_label.configure(text="credentials.json сохранён")

    def run_google_auth_action(self) -> None:
        if has_saved_google_login():
            self.run_action(
                "Выход из Google",
                logout_google_account
            )
            return

        if not CREDENTIALS_FILE.exists():
            self.show_missing_google_credentials_message()
            return

        self.run_action(
            "Вход в Google",
            login_google_account
        )

    def show_missing_google_credentials_message(self) -> None:
        message = (
            "Чтобы открыть авторизацию Google, сначала добавьте "
            "credentials.json во вкладке «Дополнительно»."
        )
        self.status_label.configure(text=message)
        self.write_log(message)
        self.refresh_status_panel()
        self.show_tab("extra")
        self.flash_credentials_button()

    def flash_credentials_button(
        self,
        step: int = 0
    ) -> None:
        pulse_colors = [
            SURFACE,
            "#fff7e6",
            "#ffe8b3",
            "#ffd166",
            "#ffe8b3",
            "#fff7e6",
            SURFACE
        ]

        if step >= len(pulse_colors):
            self._style_sidebar_button(self.credentials_button)
            return

        self.credentials_button.configure(
            fg_color=pulse_colors[step],
            border_color=WARNING,
            text_color=TEXT
        )

        self.after(
            140,
            lambda: self.flash_credentials_button(step + 1)
        )

    def ensure_google_authorized(self) -> bool:
        if has_saved_google_login():
            return True

        if not CREDENTIALS_FILE.exists():
            self.show_missing_google_credentials_message()
            return False

        message = (
            "Сначала выполните вход в аккаунт Google "
            "во вкладке «Дополнительно»."
        )
        self.status_label.configure(text=message)
        self.write_log(message)
        self.refresh_status_panel()
        self.show_tab("extra")
        self.flash_google_auth_button()

        return False

    def flash_google_auth_button(
        self,
        step: int = 0
    ) -> None:
        pulse_colors = [
            SURFACE,
            "#f2f7ff",
            "#e6f0ff",
            "#d9e8ff",
            "#e6f0ff",
            "#f2f7ff",
            SURFACE
        ]

        if step >= len(pulse_colors):
            self.refresh_google_auth_button(has_saved_google_login())
            return

        self.google_auth_button.configure(
            fg_color=pulse_colors[step],
            border_color=BLUE,
            text_color=BLUE
        )

        self.after(
            140,
            lambda: self.flash_google_auth_button(step + 1)
        )

    def run_google_required_action(self, title: str, action: Action) -> None:
        if not self.ensure_google_authorized():
            return

        self.run_action(title, action)

    def confirm_delete_calendar(self) -> None:
        if not self.ensure_google_authorized():
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Удалить календарь")
        dialog.geometry("460x230")
        dialog.resizable(False, False)
        dialog.configure(fg_color=APP_BG)
        dialog.transient(self)
        dialog.grab_set()

        icon_file = AVATAR_FILE.with_suffix(".ico")
        if icon_file.exists():
            dialog.after(
                200,
                lambda: dialog.iconbitmap(str(icon_file))
            )

        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - 460) // 2
        y = self.winfo_rooty() + (self.winfo_height() - 230) // 2
        dialog.geometry(f"460x230+{x}+{y}")

        panel = ctk.CTkFrame(
            dialog,
            fg_color=SURFACE,
            border_width=1,
            border_color=BORDER,
            corner_radius=8
        )
        panel.pack(padx=18, pady=18, fill="both", expand=True)
        panel.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(
            panel,
            fg_color="transparent"
        )
        header.grid(row=0, column=0, padx=22, pady=(20, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        if AVATAR_FILE.exists():
            delete_dialog_icon = ctk.CTkImage(
                light_image=Image.open(AVATAR_FILE),
                dark_image=Image.open(AVATAR_FILE),
                size=(34, 34)
            )
            icon_label = ctk.CTkLabel(
                header,
                text="",
                image=delete_dialog_icon
            )
            icon_label.grid(row=0, column=0, padx=(0, 12), sticky="w")
            self.delete_dialog_icon = delete_dialog_icon

        title = ctk.CTkLabel(
            header,
            text="Удалить календарь TPU?",
            text_color=TEXT,
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w"
        )
        title.grid(row=0, column=1, sticky="ew")

        label = ctk.CTkLabel(
            panel,
            text=(
                "Календарь будет удалён из Google Calendar. "
                "Это действие нельзя отменить."
            ),
            text_color=MUTED,
            wraplength=370,
            justify="left",
            anchor="w"
        )
        label.grid(row=1, column=0, padx=22, pady=(0, 18), sticky="ew")

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, padx=22, pady=(6, 22), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)

        cancel = self._make_button(
            actions,
            text="Отмена",
            command=dialog.destroy,
            outline=True
        )
        cancel.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        confirm = self._make_button(
            actions,
            text="Удалить",
            command=lambda: self._delete_after_confirm(dialog),
            danger=True
        )
        confirm.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        cancel.focus_set()

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

            if "group_verified" in result:
                if result["group_verified"]:
                    self.set_group_check_status(
                        f"Группа сохранена, id: {result['group_id']}",
                        state="ok"
                    )

                else:
                    self.set_group_check_status(
                        "Группа сохранена. Сайт ТПУ сейчас ее не подтвердил.",
                        state="warning"
                    )

                self.refresh_sidebar_info()
                self.refresh_first_run_panel()
        self.refresh_status_panel()
        self.status_label.configure(text="Готово к работе")
        self.set_busy(False)

    def _fail_action(self, title: str, error_text: str) -> None:
        self.write_log(f"{title}: ошибка")
        last_line = error_text.strip().splitlines()[-1]
        reason = self.format_error_reason(last_line)
        self.write_log(f"Причина: {reason}")
        self.write_log(error_text)
        self.status_label.configure(text="Ошибка выполнения")
        if title == "Сохранение группы":
            self.set_group_check_status(reason, state="error")
        self.set_busy(False)

    def format_error_reason(self, error_line: str) -> str:
        if ": " in error_line:
            error_type, message = error_line.split(": ", 1)

            if error_type.endswith("Error"):
                return message

        return error_line

    def write_summary(self, result: dict) -> None:
        if "credentials_imported" in result:
            self.write_log("Итог: credentials.json готов к использованию")

            if result.get("token_removed"):
                self.write_log(
                    "Итог: старый вход Google сброшен, войдите заново"
                )

            return

        if "group_verified" in result:
            if result["group_verified"]:
                self.write_log(
                    f"Итог: группа {result['group_name']} сохранена, "
                    f"id {result['group_id']}"
                )

            else:
                self.write_log(
                    f"Итог: группа {result['group_name']} сохранена, "
                    "но сайт ТПУ сейчас ее не подтвердил"
                )

            return
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
        try:
            self.subjects = load_subjects()

        except FileNotFoundError:
            self.subjects = []

        self.subject_vars = {
            subject["title"]: ctk.BooleanVar(
                value=subject.get("enabled", True)
            )
            for subject in self.subjects
        }

        self.render_subjects()

    def render_subjects(self) -> None:
        for child in self.subjects_frame.winfo_children():
            child.destroy()

        if not self.subjects:
            self.subjects_hint.configure(
                text="Список появится после обновления расписания."
            )
            return

        query = self.subject_search.get().strip().lower()
        filtered_subjects = [
            subject
            for subject in self.subjects
            if query in subject["title"].lower()
        ]
        enabled_count = sum(
            1
            for subject in self.subjects
            if self.subject_vars[subject["title"]].get()
        )

        self.subjects_hint.configure(
            text=(
                f"Включено {enabled_count} из {len(self.subjects)} предметов"
            )
        )

        for row, subject in enumerate(filtered_subjects):
            variable = self.subject_vars[subject["title"]]

            checkbox = ctk.CTkCheckBox(
                self.subjects_frame,
                text=subject["title"],
                variable=variable,
                text_color=TEXT,
                checkbox_width=18,
                checkbox_height=18,
                border_color="#6b7a90",
                fg_color=BLUE,
                hover_color="#dce9ff"
            )
            checkbox.grid(row=row, column=0, padx=8, pady=6, sticky="w")

    def set_all_subjects(self, enabled: bool) -> None:
        set_all_subjects_enabled(self.subjects, enabled)

        for variable in self.subject_vars.values():
            variable.set(enabled)

        self.render_subjects()

    def save_subjects_from_ui(self) -> None:
        if not self.subjects:
            self.write_log("Нет предметов для сохранения.")
            return

        for subject in self.subjects:
            variable = self.subject_vars[subject["title"]]
            subject["enabled"] = bool(variable.get())

        save_subjects(self.subjects)
        self.render_subjects()
        self.write_log("subjects.json сохранён.")

    def set_group_check_status(
        self,
        message: str,
        state: str
    ) -> None:
        colors = {
            "ok": GREEN,
            "warning": WARNING,
            "error": RED
        }

        self.group_check_status.configure(
            text=message,
            text_color=colors.get(state, MUTED)
        )

    def save_group_from_settings(self) -> None:
        group_name = normalize_group_name(
            self.group_entry.get()
        )

        if not group_name:
            message = "Введите группу перед сохранением."
            self.set_group_check_status(message, state="error")
            self.status_label.configure(text=message)
            self.write_log(message)
            return

        self.group_entry.delete(0, "end")
        self.group_entry.insert(0, group_name)

        def action(status_callback) -> dict:
            status_callback(f"Сохраняю группу: {group_name}")

            new_config = {
                **CONFIG,
                "group_name": group_name
            }
            save_config(new_config)
            status_callback("Группа сохранена.")
            status_callback(f"Проверяю группу на сайте ТПУ: {group_name}")

            group_id = None
            check_error = ""

            try:
                group_id = resolve_group_id(
                    group_name,
                    status_callback=status_callback
                )

            except Exception as error:
                check_error = str(error)

            if group_id:
                status_callback(f"Группа найдена на сайте ТПУ, id: {group_id}")

            else:
                status_callback(
                    "Сайт ТПУ сейчас не подтвердил группу. "
                    "Название сохранено, но синхронизация может быть недоступна, "
                    "пока расписание не появится на сайте."
                )

            return {
                "group_name": group_name,
                "group_id": group_id,
                "group_verified": bool(group_id),
                "check_error": check_error
            }

        self.run_action(
            "Сохранение группы",
            action
        )

    def save_settings(self) -> None:
        try:
            weeks_ahead = int(self.weeks_entry.get().strip())

        except ValueError:
            self.status_label.configure(
                text="Количество недель должно быть числом"
            )
            return

        if not 1 <= weeks_ahead <= 24:
            self.status_label.configure(
                text="Количество недель должно быть от 1 до 24"
            )
            return

        calendar_name = self.calendar_entry.get().strip()

        if not calendar_name:
            self.status_label.configure(
                text="Имя календаря не должно быть пустым"
            )
            return

        calendar_changed = calendar_name != CONFIG.get("calendar_name", "")
        new_config = {
            **CONFIG,
            "weeks_ahead": weeks_ahead,
            "calendar_name": calendar_name,
            "calendar_id": "" if calendar_changed else CONFIG.get("calendar_id", "")
        }
        save_config(new_config)
        self.refresh_sidebar_info()
        self.refresh_first_run_panel()
        self.status_label.configure(text="Настройки сохранены")
        self.write_log("config.json сохранён.")

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"

        for button in self.buttons:
            button.configure(state=state)

        if not busy:
            for button in self.buttons:
                if hasattr(button, "sidebar_danger"):
                    self._style_sidebar_button(
                        button,
                        danger=button.sidebar_danger
                    )

            self.refresh_status_panel()


def main() -> None:
    app = DesktopApp()
    app.mainloop()
