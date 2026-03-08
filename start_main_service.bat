@echo off
chcp 65001 >nul
echo ========================================
echo 主服务启动脚本 (Multi Free API Proxy)
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

pip show watchdog >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装 watchdog...
    pip install watchdog
)

echo.
echo [启动] 启动主服务 (端口 5000)...
echo.
echo [提示] 确保独立服务已启动（如果需要使用 free5 或 free8）
echo   - free5: 运行 start_free5_service.bat
echo   - free8: 运行 start_free8_service.bat
echo.

cd /d %~dp0multi_free_api_proxy
python multi_free_api_proxy_v3.py

pause