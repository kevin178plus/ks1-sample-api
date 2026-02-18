@echo off
chcp 65001 >nul
echo ========================================
echo 安全启动API代理 - 不修改系统
echo ========================================
echo.

:: 不做任何系统修改，只启动服务

echo 1. 检查Python环境...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python
    pause
    exit /b 1
)
echo ✅ Python已安装

echo.
echo 2. 检查依赖...
python -c "import flask" >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在安装Flask...
    pip install flask
)
python -c "import requests" >nul 2>&1
if %errorLevel% neq 0 (
    echo 正在安装Requests...
    pip install requests
)
echo ✅ 依赖检查完成

echo.
echo 3. 检查配置...
if not exist ".env" (
    echo ⚠️  未找到.env文件，请先创建并配置OPENROUTER_API_KEY
    echo 示例内容:
    echo OPENROUTER_API_KEY=sk-or-v1-your-key-here
    echo.
    set /p create_env=是否现在创建.env文件？(y/n): 
    if /i "%create_env%"=="y" (
        set /p api_key=请输入你的OpenRouter API Key: 
        echo OPENROUTER_API_KEY=%api_key% > .env
        echo ✅ .env文件已创建
    )
)

echo.
echo 4. 启动API代理服务...
echo 服务地址: http://localhost:5000
echo 健康检查: http://localhost:5000/health
echo 按 Ctrl+C 停止服务
echo.

python minimal_server_proxy.py

echo.
echo 服务已停止
