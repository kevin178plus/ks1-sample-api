@echo off
REM Build API Proxy Service

echo Building API Proxy Service...

REM Set compilation parameters
set GOOS=windows
set GOARCH=amd64
set CGO_ENABLED=0

REM Compile
go build -ldflags="-s -w" -o api-proxy.exe

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Output file: api-proxy.exe
) else (
    echo Build failed!
    exit /b 1
)