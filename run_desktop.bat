@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
  ".venv\Scripts\pythonw.exe" scripts\desktop.py
) else (
  ".venv\Scripts\python.exe" scripts\desktop.py
)
