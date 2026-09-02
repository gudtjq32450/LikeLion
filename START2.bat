@echo off
chcp 65001 >nul
title SEUL-JJEOCK FRONTEND
cd /d "%~dp0frontend"

echo [1/3] 기존 프론트엔드 포트(5173, 5174) 점유 확인...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5174 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/3] 프론트엔드 node_modules 확인...
if not exist "node_modules" (
    echo node_modules가 없습니다. 패키지를 설치합니다...
    call npm.cmd install
)

echo [3/3] 프론트엔드 서버 구동 중...
start http://localhost:5173
call npm.cmd run dev -- --port 5173

if %errorlevel% neq 0 (
    echo.
    echo [오류 발생] 위 메시지를 확인하세요.
)
pause