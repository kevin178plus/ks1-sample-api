@echo off
chcp 65001 >nul
echo ========================================
echo Multi Free API GUI Launcher
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python not found, please install Python 3.7+
    pause
    exit /b 1
)

echo [Info] Starting GUI interface...
echo.

python start_all_services_gui.py

if %errorlevel% neq 0 (
    echo [Error] GUI startup failed
    pause
)