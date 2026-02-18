@echo off
chcp 65001 >nul
title API代理守护进程
echo ========================================
echo API代理守护进程
echo ========================================
echo.
echo 此脚本会启动并管理API代理服务
echo 如果服务崩溃，会自动重启
echo.
echo 按 Ctrl+C 停止守护进程
echo.

:: 配置
set PYTHON_SCRIPT=minimal_server_proxy.py
set MAX_RESTART_ATTEMPTS=10
set RESTART_DELAY=5

:: 统计变量
set restart_count=0
set last_restart_time=0

:: 检查Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 检查脚本文件
if not exist "%PYTHON_SCRIPT%" (
    echo ❌ 未找到 %PYTHON_SCRIPT%
    pause
    exit /b 1
)

echo ✅ 守护进程配置：
echo    - 服务脚本：%PYTHON_SCRIPT%
echo    - 最大重启次数：%MAX_RESTART_ATTEMPTS% 次
echo    - 重启延迟：%RESTART_DELAY% 秒
echo.

:: 启动服务
echo [%date% %time%] 正在启动服务...
python %PYTHON_SCRIPT%
set service_pid=%errorLevel%

if %service_pid% equ 0 (
    echo [%date% %time%] ❌ 服务启动失败
    pause
    exit /b 1
)

echo [%date% %time%] ✅ 服务已启动
echo.

:daemon_loop
:: 等待服务退出
timeout /t 1 /nobreak >nul

:: 检查服务是否还在运行
tasklist /FI "PID eq %service_pid%" 2>nul | find /I /N "python.exe" >nul
if %errorLevel% equ 0 (
    :: 服务还在运行，继续等待
    goto daemon_loop
)

:: 服务已退出
echo [%date% %time%] ⚠️ 服务已退出

:: 检查重启次数
if %restart_count% geq %MAX_RESTART_ATTEMPTS% (
    echo [%date% %time%] ❌ 已达到最大重启次数 %MAX_RESTART_ATTEMPTS%，停止守护进程
    pause
    exit /b 1
)

:: 增加重启计数
set /a restart_count+=1

:: 检查重启频率（避免频繁重启）
if %restart_count% gtr 1 (
    set /a elapsed=%time:~0,2%*3600 + %time:~3,2%*60 + %time:~6,2% - %last_restart_time:~0,2%*3600 - %last_restart_time:~3,2%*60 - %last_restart_time:~6,2%
    if %elapsed% lss %RESTART_DELAY% (
        echo [%date% %time%] ⚠️ 重启过于频繁，等待 %RESTART_DELAY% 秒...
        timeout /t %RESTART_DELAY% /nobreak >nul
    )
)

:: 记录重启时间
set last_restart_time=%time%

:: 重启服务
echo [%date% %time%] 正在重启服务（第 %restart_count% 次）...
python %PYTHON_SCRIPT%
set service_pid=%errorLevel%

if %service_pid% equ 0 (
    echo [%date% %time%] ❌ 服务启动失败
    pause
    exit /b 1
)

echo [%date% %time%] ✅ 服务已重启
echo.

:: 继续监控
goto daemon_loop

:ctrl_c
echo.
echo [%date% %time%] 守护进程已停止
echo 总重启次数：%restart_count%
pause
