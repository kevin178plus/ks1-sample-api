@echo off
chcp 65001 >nul

REM ============================================
REM Go 版 API 代理服务 - 测试脚本
REM 自动测试 Go 版本的功能和性能
REM ============================================

set "SCRIPT_DIR=%~dp0"
set "WORK_DIR=%SCRIPT_DIR%api-proxy-go"
set "TEST_SCRIPT=%WORK_DIR%\test_api_proxy.py"
set "BASE_URL=http://localhost:5000"

echo [测试] Go 版 API 代理服务
echo ========================================

REM 检查服务是否运行
echo [检查] 服务状态...
python -c "import requests; r = requests.get('%BASE_URL%/health', timeout=5); exit(0 if r.status_code == 200 else 1)" 2>nul
if errorlevel 1 (
    echo [错误] 服务未运行，正在启动...
    call "%SCRIPT_DIR%050-start_api_proxy_go.bat"
    echo [等待] 等待服务启动...
    timeout /t 5 /nobreak >nul
)

REM 检查测试脚本是否存在
if not exist "%TEST_SCRIPT%" (
    echo [错误] 测试脚本不存在: %TEST_SCRIPT%
    pause
    exit /b 1
)

REM 运行测试
echo [测试] 运行自动化测试...
echo.

cd /d "%WORK_DIR%"
python test_api_proxy.py

echo.
echo [完成] 测试完成
pause
