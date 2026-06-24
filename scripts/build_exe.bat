@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m PyInstaller packaging\tpu_calendar_sync.spec
pause
