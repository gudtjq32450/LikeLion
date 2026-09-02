@echo off
chcp 65001 >nul
title SEUL-JJEOCK BACKEND
cd /d "%~dp0backend"

echo [1/3] 8000번 포트 정리 중...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/3] 백엔드 가상환경 확인 및 패키지 설치...
if not exist ".venv" (
    echo 가상환경 생성 중입니다. 잠시만 기다려주세요...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -r requirements.txt
pip install google-generativeai

echo [3/3] 백엔드 서버 구동 중...
python -m uvicorn main:app --port 8000
pause