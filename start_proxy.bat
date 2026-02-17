@echo off
setlocal enabledelayedexpansion

title ks1-simple-api

cd /d "%~dp0"

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
echo Dependency check complete, starting service...
echo.
python local_api_proxy.py
pause

