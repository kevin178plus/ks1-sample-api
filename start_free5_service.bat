@echo off
chcp 65001 >nul
echo ========================================
echo Free5 iFlow SDK 服务启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [信息] 检查依赖...
pip show iflow-sdk >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装 iflow-sdk...
    pip install iflow-sdk
)

pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装 flask...
    pip install flask
)

echo.
echo [启动] 启动 free5 服务 (端口 5005)...
echo.

cd /d %~dp0free_api_test\free5
python iflow_api_proxy.py

pause