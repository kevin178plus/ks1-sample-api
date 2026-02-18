@echo off
chcp 65001 >nul
echo ========================================
echo 防火墙恢复（可选）
echo ========================================
echo.
echo 此脚本将删除API代理服务的防火墙规则
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

echo 正在恢复防火墙规则...
echo.

:: 删除防火墙规则
echo 1. 删除防火墙规则...
netsh advfirewall firewall delete rule name="API Proxy Minimal" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✅ 防火墙规则已删除
    echo    - 规则名称：API Proxy Minimal
) else (
    echo ℹ️ 未找到防火墙规则，可能已被删除
)

echo.
echo ========================================
echo 防火墙恢复完成！
echo ========================================
echo.
echo 📋 已完成的操作：
echo - ✓ 防火墙：删除5000端口规则
echo.
echo 💡 如需要重新配置，运行：
echo    setup_firewall.bat
echo.

pause
