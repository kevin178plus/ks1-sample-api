@echo off

REM ============================================
REM API Proxy Go Startup Script
REM Auto-loads environment variables from .env
REM ============================================

set "SCRIPT_DIR=%~dp0"
set "WORK_DIR=%SCRIPT_DIR%api-proxy-go"
set "ENV_FILE=%SCRIPT_DIR%multi_free_api_proxy\.env"

echo [START] API Proxy Go
echo ========================================

REM Check if .env file exists
if not exist "%ENV_FILE%" (
    echo [WARN] .env not found: %ENV_FILE%
    echo [WARN] Using system environment variables
    goto :start_service
)

echo [CONFIG] Loading env from %ENV_FILE%...

REM Copy .env content to api-proxy-go directory (Go program will read it)
set "GO_ENV_FILE=%WORK_DIR%\.env"
echo [CONFIG] Copying env to %GO_ENV_FILE%...
copy /Y "%ENV_FILE%" "%GO_ENV_FILE%" >nul
echo [DONE] Env file ready
echo.

:start_service
echo [START] Starting API Proxy Go service...
echo.

cd /d "%WORK_DIR%"

if not exist "api-proxy.exe" (
    echo [ERROR] api-proxy.exe not found. Please build first.
    echo [TIP] Run: cd api-proxy-go && go build -o api-proxy.exe
    pause
    exit /b 1
)

if not exist "config.yaml" (
    echo [ERROR] Config file not found: %WORK_DIR%\config.yaml
    pause
    exit /b 1
)

start "API-Proxy-Go" cmd /k "color 0A & api-proxy.exe -config config.yaml"

echo [DONE] Service started
timeout /t 16
