@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
  ".venv\Scripts\pythonw.exe" desktop.py
) else (
  ".venv\Scripts\python.exe" desktop.py
)
