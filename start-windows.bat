@echo off
chcp 65001 > nul
setlocal
set "PWSH=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PWSH%" (
  echo Windows PowerShell was not found.
  pause
  exit /b 1
)
"%PWSH%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-windows.ps1"
if errorlevel 1 (
  echo.
  echo Failed to start the app. Check the message above.
  pause
  exit /b 1
)
endlocal
