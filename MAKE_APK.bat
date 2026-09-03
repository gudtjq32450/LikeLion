@echo off
chcp 65001 >nul
title 슬쩍 Android APK 생성기
cd /d "%~dp0"

echo ===================================================
echo    [슬쩍] Android APK 신규 빌드를 시작합니다.
echo ===================================================
echo.

:: 1. Java 및 Android SDK 환경변수 자동 보정
if "%JAVA_HOME%"=="" (
    if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Eclipse Adoptium\jdk-17.0.20.101-hotspot" (
        set "JAVA_HOME=C:\Users\%USERNAME%\AppData\Local\Programs\Eclipse Adoptium\jdk-17.0.20.101-hotspot"
    ) else if exist "C:\Program Files\Android\Android Studio\jbr" (
        set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
    )
)

if "%ANDROID_HOME%"=="" (
    if exist "%LOCALAPPDATA%\Android\Sdk" (
        set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
        set "ANDROID_SDK_ROOT=%LOCALAPPDATA%\Android\Sdk"
    )
)

:: 2. Frontend 최신 번들 빌드
echo [*] 1/4. 프론트엔드 웹 빌드 중 (Vite Build)...
cd /d "%~dp0frontend"
call npm.cmd run build
if %errorlevel% neq 0 (
    echo [!] 프론트엔드 빌드에 실패했습니다. 오류를 확인해 주세요.
    pause
    exit /b %errorlevel%
)

:: 3. Capacitor 안드로이드 네이티브 동기화
echo.
echo [*] 2/4. Capacitor 네이티브 동기화 중 (Capacitor Sync)...
call npx.cmd cap sync android
if %errorlevel% neq 0 (
    echo [!] Capacitor 동기화에 실패했습니다.
    pause
    exit /b %errorlevel%
)

:: 4. Gradle APK 패키징
echo.
echo [*] 3/4. 안드로이드 APK 패키징 중 (Gradle assembleDebug)...
cd /d "%~dp0frontend\android"
call gradlew.bat assembleDebug
if %errorlevel% neq 0 (
    echo [!] APK 패키징(Gradle)에 실패했습니다.
    pause
    exit /b %errorlevel%
)

:: 5. APK 복사 및 카카오톡 전송용 ZIP 자동 압축
echo.
echo [*] 4/4. 최상위 폴더로 복사 및 카카오톡/메신저용 ZIP 압축 생성 중...
cd /d "%~dp0"
copy /y "frontend\android\app\build\outputs\apk\debug\app-debug.apk" "슬쩍_debug.apk" >nul

powershell -Command "Compress-Archive -Path '슬쩍_debug.apk' -DestinationPath '슬쩍_debug.zip' -Force"

echo.
echo ===================================================
echo   [빌드 성공!] 최신 APK가 생성되었습니다.
echo ===================================================
echo   1. APK 파일 (휴대폰 설치용):
echo      - %~dp0슬쩍_debug.apk
echo.
echo   2. ZIP 파일 (카카오톡/메신저 전송용):
echo      - %~dp0슬쩍_debug.zip
echo ===================================================
echo.

explorer.exe /select,"%~dp0슬쩍_debug.apk"
pause
