@echo off
chcp 65001 >nul
echo ========================================
echo 最小化配置 - 仅API代理必要设置
echo ========================================
echo.
echo 此脚本只做API代理必需的配置，不影响其他项目
echo.

echo 1. 检查Python和依赖...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ 未安装Python，请先安装
    pause
    exit /b 1
)

python -c "import flask" >nul 2>&1 || (
    echo 安装Flask...
    pip install flask
)

python -c "import requests" >nul 2>&1 || (
    echo 安装Requests...
    pip install requests
)
echo ✅ 环境检查完成

echo.
echo 2. 创建简单的启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo title API Proxy - Minimal Setup
echo echo 启动最小化API代理...
echo echo 服务地址: http://localhost:5000
echo echo 按 Ctrl+C 停止
echo echo.
echo python minimal_server_proxy.py
echo.
echo echo 服务已停止
echo pause
) > a22-start_minimal.bat
echo ✅ 启动脚本已创建: a22-start_minimal.bat

echo.
echo ========================================
echo 最小化配置完成！
echo ========================================
echo.
echo 📋 已完成的配置：
echo - ✓ 依赖：检查Python和必要库
echo - ✓ 启动：创建了便捷启动脚本
echo.
echo ❌ 未修改的系统设置：
echo - ✗ 防火墙（保持原样）
echo - ✗ 虚拟内存（保持原样）
echo - ✗ 系统服务（保持原样）
echo - ✗ 开机任务（未创建）
echo - ✗ 其他系统配置（保持原样）
echo.
echo 💡 防火墙配置（可选）：
echo    如需要开放5000端口，请运行：
echo    b01-setup_firewall.bat（以管理员身份运行）
echo.
echo 🚀 现在可以运行：
echo    a22-start_minimal.bat
echo.
echo 💡 如需要回退，运行：
echo    b03-restore_system.bat
echo.

pause