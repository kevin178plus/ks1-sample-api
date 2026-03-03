@echo off
setlocal enabledelayedexpansion

echo Starting API Proxy Service...

set GOOS=windows
set GOARCH=amd64
set GOPROXY=https://goproxy.cn,direct

REM Check if executable exists
if not exist "api-proxy.exe" (
    echo Building executable...
    go build -ldflags="-s -w" -o api-proxy.exe
    if !errorlevel! neq 0 (
        echo Build failed!
        pause
        exit /b 1
    )
)

REM Run the service
echo Starting service on port 5000...
.\api-proxy.exe -config config.yaml

pause