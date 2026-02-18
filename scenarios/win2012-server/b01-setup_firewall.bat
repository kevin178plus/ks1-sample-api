@echo off
chcp 65001 >nul
echo ========================================
echo 防火墙配置（可选）
echo ========================================
echo.
echo 此脚本将配置防火墙规则，允许访问API代理服务的5000端口
echo.
echo ⚠️ 注意：此操作需要管理员权限
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 错误：需要管理员权限
    echo 请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo 正在配置防火墙规则...
echo.

:: 删除旧规则（如果存在）
echo 1. 删除旧规则（如果存在）...
netsh advfirewall firewall delete rule name="API Proxy Minimal" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 已删除旧规则
) else (
    echo ℹ️ 未找到旧规则
)

:: 添加新规则
echo.
echo 2. 添加新规则...
netsh advfirewall firewall add rule name="API Proxy Minimal" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 防火墙规则已添加
    echo    - 规则名称：API Proxy Minimal
    echo    - 方向：入站
    echo    - 动作：允许
    echo    - 协议：TCP
    echo    - 端口：5000
) else (
    echo ❌ 添加防火墙规则失败
    echo    错误代码：%errorLevel%
    pause
    exit /b 1
)

echo.
echo ========================================
echo 防火墙配置完成！
echo ========================================
echo.
echo 📋 已完成的配置：
echo - ✓ 防火墙：开放5000端口
echo.
echo 💡 如需要回退，运行：
echo    restore_firewall.bat
echo.

pause
