@echo off
chcp 65001 >nul
title 슬쩍 APK 빌드 스크립트
cd /d "%~dp0"

echo ===================================================
echo   [슬쩍] Android APK 빌드를 시작합니다.
echo ===================================================

:: 1. Frontend 빌드
echo [*] 1/3. 프론트엔드 웹 번들 빌드 중 (Vite)...
cd /d "%~dp0frontend"
call npm.cmd run build
if %errorlevel% neq 0 (
    echo [!] 프론트엔드 빌드에 실패했습니다.
    pause
    exit /b %errorlevel%
)

:: 2. Capacitor 안드로이드 동기화
echo [*] 2/3. Capacitor 동기화 중...
call npx.cmd cap sync android
if %errorlevel% neq 0 (
    echo [!] Capacitor 동기화에 실패했습니다.
    pause
    exit /b %errorlevel%
)

:: 3. Gradle APK 빌드
echo [*] 3/3. 안드로이드 APK 패키징 중 (Gradle assembleDebug)...
cd /d "%~dp0frontend\android"
call gradlew.bat assembleDebug
if %errorlevel% neq 0 (
    echo [!] APK 빌드에 실패했습니다.
    pause
    exit /b %errorlevel%
)

:: 4. APK 파일 복사
cd /d "%~dp0"
copy /y "frontend\android\app\build\outputs\apk\debug\app-debug.apk" "슬쩍_debug.apk" >nul

echo.
echo ===================================================
echo   [성공] APK 생성이 완료되었습니다!
echo   파일 위치: %~dp0슬쩍_debug.apk
echo ===================================================
echo.
explorer.exe /select,"%~dp0슬쩍_debug.apk"
pause
