@echo off
setlocal enabledelayedexpansion

title ks1-multi-free-api-v3

cd /d "%~dp0"

echo ============================================
echo      多Free API代理服务启动脚本 (V3)
echo ============================================
echo.

REM 设置默认端口
set PORT=5000

REM 检查是否设置了自定义端口
if not "%1"=="" (
    set PORT=%1
)

echo [启动] 端口: %PORT%
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

REM 检查调试模式
if exist DEBUG_MODE.txt (
    echo [调试] 调试模式已启用
    echo [调试] 可访问 http://localhost:%PORT%/debug 查看调试面板
    echo.
) else (
    echo [调试] 调试模式未启用 ^(创建 DEBUG_MODE.txt 文件以启用^)
    echo.
)

echo Dependency check complete, starting service...
echo.
echo [启动] 正在启动多Free API代理服务 (V3)...
echo.

REM 启动服务
python multi_free_api_proxy_v3.py

echo.
echo 服务已停止
pause
