@echo off
chcp 65001 >nul
echo ========================================
echo Free8 Friendli.ai 服务启动脚本
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
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装 flask...
    pip install flask
)

pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装 requests...
    pip install requests
)

echo.
echo [启动] 启动 free8 服务 (端口 5008)...
echo.

cd /d %~dp0free_api_test\free8
python friendli_service.py

pause