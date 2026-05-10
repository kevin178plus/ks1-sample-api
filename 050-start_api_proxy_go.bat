@echo off
chcp 65001 >nul

REM ============================================
REM API Proxy Go 启动脚本
REM 自动从 .env 加载环境变量
REM ============================================

set "SCRIPT_DIR=%~dp0"
set "WORK_DIR=%SCRIPT_DIR%api-proxy-go"
set "ENV_FILE=%SCRIPT_DIR%multi_free_api_proxy\.env"

echo [启动] API Proxy Go 版
echo ========================================

REM 检查 .env 文件是否存在
if not exist "%ENV_FILE%" (
    echo [警告] .env 文件不存在: %ENV_FILE%
    echo [警告] 将使用系统环境变量
    goto :start_service
)

echo [配置] 从 %ENV_FILE% 加载环境变量...

REM 逐行读取 .env 文件
for /f "usebackq tokens=1,* delims== eol=#" %%a in ("%ENV_FILE%") do (
    set "line=%%a"
    set "val=%%b"
    
    REM 去除前后空格后的key
    for /f "tokens=1" %%k in ("!line!") do set "key=%%k"
    
    REM 跳过空行
    if defined key (
        REM 设置环境变量（跳过空值）
        if defined val (
            set "!key!=!val!"
        )
    )
)

echo [完成] 环境变量加载完毕
echo.

:start_service
echo [启动] 启动 API Proxy Go 服务...
echo.

cd /d "%WORK_DIR%"

if not exist "api-proxy-go.exe" (
    echo [错误] api-proxy-go.exe 不存在，请先编译
    echo [提示] 运行: cd api-proxy-go ^&^& go build -o api-proxy-go.exe
    pause
    exit /b 1
)

if not exist "config.yaml" (
    echo [错误] 配置文件不存在: %WORK_DIR%\config.yaml
    pause
    exit /b 1
)

start "API-Proxy-Go" cmd /k "color 0A & api-proxy-go.exe -config config.yaml"

echo [完成] 服务已启动
timeout /t 16
