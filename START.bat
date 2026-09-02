@echo off
chcp 65001 >nul
title SEUL-JJEOCK RUNNER
cd /d "%~dp0"

echo ===================================================
echo   슬쩍 (SEUL-JJEOCK) 서비스 시작 중...
echo ===================================================

:: 1. 백엔드 폴더 확인
if not exist "backend" (
    echo [오류] backend 폴더를 찾을 수 없습니다.
    echo run.bat 파일이 프로젝트 루트 폴더에 있는지 확인해주세요.
    pause
    exit /b
)

:: 2. 기존 8000 포트 프로세스 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 3. 가상환경 확인 및 패키지 설치
cd /d "%~dp0backend"
if not exist ".venv" (
    echo [*] 파이썬 가상환경 생성 중...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
echo [*] 필수 라이브러리 확인 및 설치 중...
python -m pip install -q fastapi uvicorn pydantic python-dotenv google-generativeai sqlalchemy "python-jose[cryptography]" "pydantic[email]"

:: 4. 백엔드와 프론트엔드 동시 실행 (창 이름 따옴표 에러 방지 처리)
echo [*] 백엔드 및 프론트엔드 서버를 켭니다.

start "BACKEND" cmd /k "cd /d %~dp0backend && call .venv\Scripts\activate.bat && python -m uvicorn main:app --port 8000"

start "FRONTEND" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ===================================================
echo   실행 완료!
echo   브라우저 주소: http://localhost:5173
echo ===================================================
pause