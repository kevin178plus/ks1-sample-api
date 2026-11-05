@echo off
rem VERSION: v1.0 build 2
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [INFO] vllm alias proxy - starting ...

if not exist "vllm_alias_proxy.py" (
    echo [ERROR] missing vllm_alias_proxy.py
    goto :fail
)
if not exist "proxy_config.json" (
    echo [ERROR] missing proxy_config.json
    goto :fail
)

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] python not found in PATH
    goto :fail
)

if exist "server.pid" (
    set /p OLD_PID=<server.pid
    powershell -NoProfile -Command "if (Get-Process -Id !OLD_PID! -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >nul 2>&1
    if !ERRORLEVEL! EQU 1 (
        echo [WARN] service already running - PID !OLD_PID!
        goto :done
    )
    del server.pid >nul 2>&1
    del server.port >nul 2>&1
)

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 18010 -State Listen -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }" >nul 2>&1
if %ERRORLEVEL% EQU 1 (
    echo [ERROR] port 18010 is already in use
    goto :fail
)

if exist "server.err.log" del server.err.log >nul 2>&1
start "vllm-alias-proxy" /MIN python "vllm_alias_proxy.py"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] failed to launch python
    goto :fail
)

timeout /t 2 /nobreak >nul

if exist "server.pid" (
    set /p NEW_PID=<server.pid
    echo [OK] service started - PID !NEW_PID! - port 18010
) else (
    echo [WARN] server.pid not found - check server.log
)

:done
endlocal
exit /b 0

:fail
endlocal
exit /b 1
