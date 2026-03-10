@echo off
chcp 65001 >nul
echo ========================================
echo 多Free API代理服务 - 一键启动脚本
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
    echo [安装] 安装flask...
    pip install flask
)

pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装requests...
    pip install requests
)

pip show watchdog >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装watchdog...
    pip install watchdog
)

echo.
echo ========================================
echo 启动服务中...
echo ========================================
echo.

REM 启动 free5 独立服务
echo [1/3] 启动 free5 独立服务 (端口 5005)...
start "free5-service" cmd /k "cd /d %~dp0free_api_test\free5 && python iflow_api_proxy.py"

REM 启动 free8 独立服务
echo [2/3] 启动 free8 独立服务 (端口 5008)...
start "free8-service" cmd /k "cd /d %~dp0free_api_test\free8 && python friendli_service.py"

REM 等待独立服务启动
echo [等待] 等待独立服务启动...
timeout /t 3 /nobreak >nul

REM 启动主服务（优化版）
echo [3/3] 启动主服务 (端口 5000, 优化版)...
cd /d %~dp0multi_free_api_proxy
python multi_free_api_proxy_v3_optimized.py

pause