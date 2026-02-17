@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title ks1-simple-api Daemon

cd /d "%~dp0"

echo ========================================
echo   ks1-simple-api Daemon Launcher
echo ========================================
echo.

if "%~1"=="" goto menu
if "%~1"=="start" goto start_daemon
if "%~1"=="stop" goto stop_daemon
if "%~1"=="status" goto status_daemon
if "%~1"=="restart" goto restart_daemon
goto menu

:menu
echo Usage: start_proxy_daemon.bat [command]
echo.
echo Commands:
echo   start   - Start daemon (recommended)
echo   stop    - Stop daemon
echo   status  - Check daemon status
echo   restart - Restart daemon
echo.
echo Example:
echo   start_proxy_daemon.bat start
echo.

set /p choice=Enter command (start/stop/status/restart): 
if "!choice!"=="start" goto start_daemon
if "!choice!"=="stop" goto stop_daemon
if "!choice!"=="status" goto status_daemon
if "!choice!"=="restart" goto restart_daemon
echo Invalid command
goto menu

:start_daemon
echo Starting daemon...
echo.
python daemon.py start
echo.
echo Daemon started
echo Log file: daemon.log
echo.
echo Press any key to exit (daemon runs in background)...
pause >nul
goto :eof

:stop_daemon
echo Stopping daemon...
python daemon.py stop
echo.
pause >nul
goto :eof

:status_daemon
python daemon.py status
echo.
pause >nul
goto :eof

:restart_daemon
echo Restarting daemon...
python daemon.py restart
echo.
pause >nul
goto :eof
