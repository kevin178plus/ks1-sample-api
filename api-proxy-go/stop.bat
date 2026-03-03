@echo off
echo Stopping API Proxy Service...
echo.

taskkill /F /IM api-proxy.exe

echo.
timeout /t 2 /nobreak