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

scripts/
  desktop.py           запуск desktop-приложения
  main.py              запуск консольного меню
  install_shortcut.*   создание ярлыка на рабочем столе
  build_exe.bat        сборка exe через PyInstaller

packaging/
  tpu_calendar_sync.spec  настройки PyInstaller

run_desktop.bat        быстрый запуск desktop-приложения из корня проекта
```

## Установка для разработки

```powershell
cd path\to\TPU-Calendar-Sync
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Расписание загружается обычным HTTP-запросом без отдельного браузера.

## Google Calendar

В desktop-приложении откройте вкладку `Дополнительно` и нажмите `Выбрать credentials.json`. Приложение скопирует OAuth-файл в:

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
.\.venv\Scripts\python.exe scripts\desktop.py
```

Или двойным кликом:

```text
run_desktop.bat
```

Консольное меню:

```powershell
.\.venv\Scripts\python.exe scripts\main.py
```

## Ярлык на рабочем столе

Запустите:

```text
scripts\install_shortcut.bat
```

Скрипт создаст ярлык `TPU Calendar Sync` на рабочем столе с иконкой приложения.

## Сборка exe

Установите зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Соберите приложение:

```text
scripts\build_exe.bat
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

Если запускаете exe впервые, выберите `credentials.json` во вкладке `Дополнительно`. Файл будет сохранён в:

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

## Тесты

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s . -p "*test*.py"
```

## Примечания

- `data/`, `credentials.json`, `token.json`, `parsed_schedule.json`, `subjects.json`, `logs/`, `build/`, `dist/` не коммитятся.
- Парсер зависит от HTML-разметки сайта ТПУ. Если сайт изменится, приложение покажет ошибку `ScheduleParseError`.
- Парсер и ключевые сценарии синхронизации покрыты `unittest`; HTML-примеры лежат в `tests/fixtures/`.
