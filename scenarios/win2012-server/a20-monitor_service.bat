@echo off
chcp 65001 >nul
title API Proxy Monitor
echo ========================================
echo API Proxy Monitor Script
echo ========================================
echo.
echo This script monitors the API proxy service
echo If service stops, it will auto restart
echo.
echo Press Ctrl+C to stop monitoring
echo.

:: Configuration
set CHECK_INTERVAL=30
set MAX_RESTART_ATTEMPTS=10
set RESTART_DELAY=5
set PYTHON_SCRIPT=minimal_server_proxy.py
set LOCK_FILE=.service_running.lock

:: Statistics
set restart_count=0

:: Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found, please install Python first
    pause
    exit /b 1
)

echo [OK] Monitor Configuration:
echo    - Check Interval: %CHECK_INTERVAL% seconds
echo    - Max Restart Attempts: %MAX_RESTART_ATTEMPTS% times
echo    - Restart Delay: %RESTART_DELAY% seconds
echo    - Monitor Script: %PYTHON_SCRIPT%
echo.

:monitor_loop
:: Check if service is running (by checking port 5000)
netstat -ano | find ":5000" | find "LISTENING" >nul
if %errorLevel% equ 0 (
    :: Service is running
    if %restart_count% gtr 0 (
        echo [%date% %time%] Service running normally (restarted %restart_count% times)
    )
) else (
    :: Service not running
    echo [%date% %time%] [WARNING] Service not running, attempting to restart...

    :: Check restart count
    if %restart_count% geq %MAX_RESTART_ATTEMPTS% (
        echo [%date% %time%] [ERROR] Max restart attempts %MAX_RESTART_ATTEMPTS% reached, stopping monitor
        pause
        exit /b 1
    )

    :: Increment restart count
    set /a restart_count+=1

    :: Restart service
    echo [%date% %time%] Starting service...
    start /MIN python %PYTHON_SCRIPT%

    :: Wait for service to start
    timeout /t 5 /nobreak >nul

    :: Check if started successfully
    netstat -ano | find ":5000" | find "LISTENING" >nul
    if %errorLevel% equ 0 (
        echo [%date% %time%] [OK] Service started successfully (restart #%restart_count%)
    ) else (
        echo [%date% %time%] [ERROR] Service start failed
    )
)

:: Wait for next check
timeout /t %CHECK_INTERVAL% /nobreak >nul

:: Continue monitoring
goto monitor_loop

:ctrl_c
echo.
echo [%date% %time%] Monitor stopped
echo Total restarts: %restart_count%
pause
