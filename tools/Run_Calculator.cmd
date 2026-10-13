@echo off
setlocal
cd /d "%~dp0.."
if not exist "venv\Scripts\python.exe" (
  echo Development environment not found: %cd%\venv
  echo Run tools\dev_shell.sh from Git Bash to create the environment.
  pause
  exit /b 1
)
"venv\Scripts\python.exe" -m src.main
if errorlevel 1 pause
