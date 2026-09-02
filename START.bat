@echo off
title SEUL-JJEOCK BACKEND
cd /d "%~dp0backend"

:: 1. Clear Port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Check Virtual Environment
if not exist ".venv" (
    echo [*] Creating virtual environment...
    python -m venv .venv
)

:: 3. Activate and Install Packages
call .venv\Scripts\activate.bat
python -m pip install -q fastapi uvicorn pydantic python-dotenv google-generativeai

:: 4. Start FastAPI Server
echo [*] Starting FastAPI Server on port 8000...
python -m uvicorn main:app --port 8000

if %errorlevel% neq 0 (
    echo.
    echo [*] Server exited with error.
)
pause