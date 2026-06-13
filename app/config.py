import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "config.json"
PARSED_SCHEDULE_FILE = BASE_DIR / "parsed_schedule.json"
SUBJECTS_FILE = BASE_DIR / "subjects.json"
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"
LOGS_DIR = BASE_DIR.parent / "logs"
ASSETS_DIR = BASE_DIR / "assets"
AVATAR_FILE = ASSETS_DIR / "avatar.png"


with open(
    CONFIG_FILE,
    "r",
    encoding="utf-8"
) as file:

    CONFIG = json.load(file)
