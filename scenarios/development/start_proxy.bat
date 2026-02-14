@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo Starting local API proxy service...
echo.
echo Checking dependencies...
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependency: watchdog
    pip install watchdog
)
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependency: flask
    pip install flask
)
pip show requests >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependency: requests
    pip install requests
)
echo.
echo Dependencies check completed, starting service...
echo.
python local_api_proxy.py
pause
