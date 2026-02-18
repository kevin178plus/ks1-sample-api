@echo off
chcp 65001 >nul
title API代理监控脚本
echo ========================================
echo API代理监控脚本
echo ========================================
echo.
echo 此脚本会定期检查API代理服务状态
echo 如果服务停止，会自动重启
echo.
echo 按 Ctrl+C 停止监控
echo.

:: 配置
set CHECK_INTERVAL=30
set MAX_RESTART_ATTEMPTS=10
set RESTART_DELAY=5
set PYTHON_SCRIPT=minimal_server_proxy.py

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

echo ✅ 监控配置：
echo    - 检查间隔：%CHECK_INTERVAL% 秒
echo    - 最大重启次数：%MAX_RESTART_ATTEMPTS% 次
echo    - 重启延迟：%RESTART_DELAY% 秒
echo    - 监控脚本：%PYTHON_SCRIPT%
echo.

:monitor_loop
:: 检查服务是否运行
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq API*" 2>nul | find /I /N "python.exe" >nul
if %errorLevel% equ 0 (
    :: 服务正在运行
    if %restart_count% gtr 0 (
        echo [%date% %time%] 服务正常运行（已重启 %restart_count% 次）
    )
) else (
    :: 服务未运行
    echo [%date% %time%] ⚠️ 服务未运行，尝试重启...

    :: 检查重启次数
    if %restart_count% geq %MAX_RESTART_ATTEMPTS% (
        echo [%date% %time%] ❌ 已达到最大重启次数 %MAX_RESTART_ATTEMPTS%，停止监控
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
    echo [%date% %time%] 正在启动服务...
    start /B python %PYTHON_SCRIPT% >nul 2>&1

    :: 等待服务启动
    timeout /t 3 /nobreak >nul

    :: 检查是否启动成功
    tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq API*" 2>nul | find /I /N "python.exe" >nul
    if %errorLevel% equ 0 (
        echo [%date% %time%] ✅ 服务启动成功（第 %restart_count% 次重启）
    ) else (
        echo [%date% %time%] ❌ 服务启动失败
    )
)

:: 等待下一次检查
timeout /t %CHECK_INTERVAL% /nobreak >nul

:: 继续监控
goto monitor_loop

:ctrl_c
echo.
echo [%date% %time%] 监控已停止
echo 总重启次数：%restart_count%
pause
