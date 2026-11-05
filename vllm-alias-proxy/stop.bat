@echo off
rem VERSION: v1.0 build 1
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [INFO] vllm alias proxy - stopping ...

if not exist "server.pid" (
    echo [WARN] server.pid not found - nothing to stop
    goto :done
)

set /p TARGET_PID=<server.pid
taskkill /F /PID !TARGET_PID! >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    echo [OK] service stopped - PID !TARGET_PID!
) else (
    echo [WARN] process not found - PID !TARGET_PID!
)

del server.pid >nul 2>&1
del server.port >nul 2>&1

:done
endlocal
exit /b 0
