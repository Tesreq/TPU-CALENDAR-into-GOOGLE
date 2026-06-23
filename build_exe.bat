@echo off
cd /d "%~dp0"
".venv\Scripts\python.exe" -m PyInstaller tpu_calendar_sync.spec
pause
