@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo      多Free API代理服务启动脚本
echo ============================================
echo.

REM 设置默认端口
set PORT=5000

REM 检查是否设置了自定义端口
if not "%1"=="" (
    set PORT=%1
)

echo [启动] 端口: %PORT%
echo [启动] 正在启动多Free API代理服务...
echo.

REM 启动服务
python multi_free_api_proxy.py

echo.
echo 服务已停止
pause
