@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 本地 API 代理服务启动 (优化版)
echo ========================================
echo.

:: 检查Python环境
echo 1. 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python已安装

:: 检查必需依赖
echo.
echo 2. 检查必需依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 安装Flask...
    pip install flask
)

pip show requests >nul 2>&1
if errorlevel 1 (
    echo 安装Requests...
    pip install requests
)

:: 检查可选依赖
echo.
echo 3. 检查可选依赖...
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo 安装Watchwatchdog (用于文件监控)...
    pip install watchdog
    echo ✅ 文件监控功能已启用
) else (
    echo ✅ Watchwatchdog已安装
)

:: 检查配置文件
echo.
echo 4. 检查配置文件...
if not exist ".env" (
    echo ⚠️  未找到.env文件
    set /p create_env=是否现在创建.env文件？(y/n): 
    if /i "!create_env!"=="y" (
        echo.
        echo 请输入OpenRouter API Key (或按Enter跳过):
        set /p api_key=
        if not "!api_key!"=="" (
            echo OPENROUTER_API_KEY=!api_key! > .env
            echo CACHE_DIR=./cache >> .env
            echo ✅ .env文件已创建
        )
    )
)

:: 启动服务
echo.
echo 5. 启动服务...
echo ========================================
echo 服务信息:
echo - 地址: http://localhost:5000
echo - API端点: http://localhost:5000/v1/chat/completions
echo - 健康检查: http://localhost:5000/health
echo - 调试面板: http://localhost:5000/debug (如果启用调试模式)
echo ========================================
echo.
echo 按 Ctrl+C 停止服务
echo.

python local_api_proxy.py

echo.
echo 服务已停止