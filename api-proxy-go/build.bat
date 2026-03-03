@echo off
REM 编译 API 代理服务

echo 正在编译 API 代理服务...

REM 设置编译参数
set GOOS=windows
set GOARCH=amd64
set CGO_ENABLED=0

REM 编译
go build -ldflags="-s -w" -o api-proxy.exe

if %ERRORLEVEL% EQU 0 (
    echo 编译成功！
    echo 输出文件: api-proxy.exe
) else (
    echo 编译失败！
    exit /b 1
)