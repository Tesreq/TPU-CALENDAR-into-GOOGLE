import json
import shutil
import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    APP_DIR = Path(sys.executable).resolve().parent
    BUNDLED_APP_DIR = Path(
        getattr(sys, "_MEIPASS", APP_DIR)
    ) / "app"
    DATA_DIR = APP_DIR / "data"

else:
    APP_DIR = PROJECT_DIR
    BUNDLED_APP_DIR = PACKAGE_DIR
    DATA_DIR = PROJECT_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"
DEFAULT_CONFIG_FILE = BUNDLED_APP_DIR / "default_config.json"
PARSED_SCHEDULE_FILE = DATA_DIR / "parsed_schedule.json"
SUBJECTS_FILE = DATA_DIR / "subjects.json"
CREDENTIALS_FILE = DATA_DIR / "credentials.json"
TOKEN_FILE = DATA_DIR / "token.json"
LOGS_DIR = APP_DIR / "logs"
ASSETS_DIR = BUNDLED_APP_DIR / "assets"
AVATAR_FILE = ASSETS_DIR / "avatar.png"

if not CONFIG_FILE.exists() and DEFAULT_CONFIG_FILE.exists():
    shutil.copyfile(
        DEFAULT_CONFIG_FILE,
        CONFIG_FILE
    )


with open(
    CONFIG_FILE,
    "r",
    encoding="utf-8"
) as file:

    CONFIG = json.load(file)


def load_config() -> dict:
    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def reload_config() -> dict:
    CONFIG.clear()
    CONFIG.update(load_config())

    return CONFIG


def save_config(config: dict) -> None:
    CONFIG.clear()
    CONFIG.update(config)

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            CONFIG,
            file,
            ensure_ascii=False,
            indent=2
        )

