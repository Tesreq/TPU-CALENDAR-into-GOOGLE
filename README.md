# TPU Calendar Sync

Desktop-приложение для синхронизации расписания группы ТПУ с Google Calendar.

## Возможности

- загрузка расписания с сайта ТПУ;
- выбор предметов, которые попадут в календарь;
- синхронизация занятий в отдельный Google Calendar;
- обновление существующих событий;
- удаление устаревших событий только в диапазоне текущего расписания;
- desktop-интерфейс с журналом, предметами и настройками;
- создание ярлыка на рабочем столе.

## Структура

```text
app/
  desktop_app.py       desktop-интерфейс
  app_actions.py       действия для GUI и CLI
  parser.py            парсер расписания ТПУ
  sync_to_json.py      загрузка расписания в JSON
  sync_calendar.py     синхронизация Google Calendar
  calendar_api.py      авторизация Google API
  config.py            пути, default_config.json и data/config.json
  default_config.json    безличный конфиг по умолчанию
  assets/              иконки приложения

desktop.py             запуск desktop-приложения
main.py                запуск консольного меню
run_desktop.bat        быстрый запуск desktop-приложения
install_shortcut.bat   создание ярлыка на рабочем столе
build_exe.bat          сборка exe через PyInstaller
```

## Установка для разработки

```powershell
cd path\to\TPU-Calendar-Sync
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Если Playwright Chromium ещё не установлен:

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
```

## Google Calendar

В папку `app` положите OAuth-файл:

```text
data/credentials.json
```

При первом подключении Google Calendar приложение откроет браузер для входа и создаст:

```text
data/token.json
```

Эти файлы добавлены в `.gitignore` и не должны попадать в репозиторий.

## Запуск

Desktop-приложение:

```powershell
.\.venv\Scripts\python.exe desktop.py
```

Или двойным кликом:

```text
run_desktop.bat
```

Консольное меню:

```powershell
.\.venv\Scripts\python.exe main.py
```

## Ярлык на рабочем столе

Запустите:

```text
install_shortcut.bat
```

Скрипт создаст ярлык `TPU Calendar Sync` на рабочем столе с иконкой приложения.

## Сборка exe

Установите зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Соберите приложение:

```text
build_exe.bat
```

Готовый файл появится в:

```text
dist/TPU Calendar Sync.exe
```

Для exe-версии пользовательские файлы хранятся рядом с программой:

```text
dist/
  TPU Calendar Sync.exe
  data/
    config.json
    credentials.json
    token.json
    parsed_schedule.json
    subjects.json
  logs/
    sync.log
```

Если запускаете exe впервые, положите `credentials.json` в:

```text
dist/data/credentials.json
```

## Настройки

Настройки можно менять во вкладке `Настройки`:

- группа;
- количество недель;
- имя календаря.

В режиме разработки они сохраняются в:

```text
data/config.json
```

В exe-режиме они сохраняются в:

```text
data/config.json
```

## Примечания

- `data/`, `credentials.json`, `token.json`, `parsed_schedule.json`, `subjects.json`, `logs/`, `build/`, `dist/` не коммитятся.
- Парсер зависит от HTML-разметки сайта ТПУ. Если сайт изменится, приложение покажет ошибку `ScheduleParseError`.
- Для полноценного релиза стоит добавить тесты парсера на сохранённых HTML-примерах.

