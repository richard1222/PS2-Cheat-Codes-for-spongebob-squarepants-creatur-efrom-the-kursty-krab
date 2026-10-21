@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher was not found. Please send this message in chat.
  pause
  exit /b 1
)
py "%~dp0tools\menu_collector_gui.py"
if errorlevel 1 (
  echo Please send the error shown above in chat.
  pause
)
