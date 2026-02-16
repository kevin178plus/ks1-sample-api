@echo off
setlocal enabledelayedexpansion

title ks1-simple-api

cd /d "%~dp0"

echo 启动本地 API 代理服务...
echo.
echo 检查依赖...
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo 安装缺失的依赖: watchdog
    pip install watchdog
)
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 安装缺失的依赖: flask
    pip install flask
)
pip show requests >nul 2>&1
if errorlevel 1 (
    echo 安装缺失的依赖: requests
    pip install requests
)
echo.
echo 依赖检查完成，启动服务...
echo.
python local_api_proxy.py
pause
