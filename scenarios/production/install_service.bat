@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 安全版 API 代理服务安装脚本
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 需要管理员权限来安装服务
    echo 请右键以管理员身份运行此脚本
    pause
    exit /b 1
)

:: 设置变量
set SERVICE_NAME=SecureAPIProxy
set SERVICE_DISPLAY=Secure API Proxy Service
set SERVICE_DESC=安全的API代理服务，转发请求到OpenRouter
set PYTHON_EXE=python
set SCRIPT_PATH=%~dp0secure_api_proxy.py
set LOG_PATH=%~dp0api_proxy.log

echo 服务配置信息:
echo  - 服务名: %SERVICE_NAME%
echo  - 脚本路径: %SCRIPT_PATH%
echo  - 日志路径: %LOG_PATH%
echo.

:: 检查Python和依赖
echo 检查依赖...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

python -c "import flask, requests, watchdog" >nul 2>&1
if %errorLevel% neq 0 (
    echo 安装缺失的依赖...
    python -m pip install flask requests watchdog
    if %errorLevel% neq 0 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

:: 检查配置文件
if not exist "%~dp0.env" (
    if not exist "%~dp0.env.production" (
        echo 错误: 未找到 .env 或 .env.production 配置文件
        echo 请先配置环境变量文件
        pause
        exit /b 1
    )
)

:: 创建服务安装脚本
set SERVICE_SCRIPT=%~dp0service_wrapper.py
(
echo import subprocess
echo import sys
echo import os
echo from pathlib import Path
echo.
echo if __name__ == '__main__':  
echo     script_dir = Path(__file__).parent
echo     proxy_script = script_dir / 'secure_api_proxy.py'
echo     log_file = script_dir / 'api_proxy.log'
echo.     
echo     try:
echo         # 重定向输出到日志文件
echo         with open(log_file, 'a', encoding='utf-8') as f:
echo             subprocess.run\((
echo                 sys.executable, 
echo                 str\(proxy_script\)
echo             \), cwd=script_dir, check=True,
echo             stdout=f, stderr=f\)
echo     except Exception as e:
echo         with open\(log_file, 'a', encoding='utf-8'\) as f:
echo             f.write\(f"Service error: {e}\\n"\)
) > "%SERVICE_SCRIPT%"

:: 使用sc命令安装服务
echo 安装Windows服务...
sc create %SERVICE_NAME^
    binPath= "%PYTHON_EXE% \"%SERVICE_SCRIPT%\""^
    DisplayName= "%SERVICE_DISPLAY%"^
    Description= "%SERVICE_DESC%"^
    start= auto

if %errorLevel% neq 0 (
    echo 错误: 服务安装失败
    pause
    exit /b 1
)

:: 配置服务恢复选项
echo 配置服务恢复选项...
sc failure %SERVICE_NAME^
    reset= 86400^
    actions= restart/5000/restart/15000/none

:: 设置服务描述
sc description %SERVICE_NAME^
    "%SERVICE_DESC% - 提供安全的API代理服务"

:: 创建防火墙规则（可选）
set /p create_firewall=是否创建防火墙规则允许端口5000访问？(y/n): 
if /i "!create_firewall!"=="y" (
    echo 创建防火墙规则...
    netsh advfirewall firewall add rule name="%SERVICE_NAME%" dir=in action=allow protocol=TCP localport=5000
    if %errorLevel% equ 0 (
        echo 防火墙规则创建成功
    ) else (
        echo 警告: 防火墙规则创建失败，请手动配置
    )
)

echo.
echo ========================================
echo 服务安装完成！
echo ========================================
echo.
echo 服务管理命令:
echo   启动服务:   net start %SERVICE_NAME%
echo   停止服务:   net stop %SERVICE_NAME%
echo   查看状态:   sc query %SERVICE_NAME%
echo   删除服务:   sc delete %SERVICE_NAME%
echo.
echo 日志文件位置: %LOG_PATH%
echo.
echo 现在是否启动服务？(y/n)
set /p start_service=
if /i "!start_service!"=="y" (
    echo 启动服务...
    net start %SERVICE_NAME%
    if %errorLevel% equ 0 (
        echo 服务启动成功！
        echo 请等待几秒钟后访问 http://localhost:5000/health 检查服务状态
    ) else (
        echo 服务启动失败，请检查日志文件
    )
)

pause