@echo off
chcp 65001 >nul
echo ========================================
echo Windows Server 2012 R2 系统优化
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请以管理员身份运行此脚本
    pause
    exit /b 1
)

echo 1. 优化虚拟内存设置...
:: 设置虚拟内存为物理内存的1.5倍
wmic computersystem where name="%computername%" set AutomaticManagedPagefile=False
wmic pagefileset where name="C:\\pagefile.sys" set InitialSize=3072,MaximumSize=3072

echo.
echo 2. 禁用不必要的服务...
:: 禁用一些不必要的服务以节省内存
sc config "Themes" start= disabled >nul 2>&1
sc config "DesktopWindowManager" start= disabled >nul 2>&1
sc config "Windows Search" start= disabled >nul 2>&1
echo 已禁用图形界面相关服务

echo.
echo 3. 配置防火墙规则...
:: 清理旧规则
netsh advfirewall firewall delete rule name="API Proxy" >nul 2>&1
:: 添加新规则
netsh advfirewall firewall add rule name="API Proxy" dir=in action=allow protocol=TCP localport=5000 profile=any

echo.
echo 4. 创建服务启动脚本...
(
echo @echo off
echo cd /d "%~dp0"
echo title API Proxy Service
echo echo 启动最小化API代理服务...
echo python minimal_server_proxy.py
echo echo 服务异常退出，10秒后重启...
echo timeout /t 10 /nobreak >nul
echo goto :eof
) > start_api_service.bat

echo.
echo 5. 创建开机自启动任务...
schtasks /delete /tn "API Proxy Auto Start" /f >nul 2>&1
schtasks /create /tn "API Proxy Auto Start" /tr "c:\%~dp0start_api_service.bat" /sc onlogon /ru SYSTEM /rl highest /f

echo.
echo 6. 系统信息检查...
echo 当前内存使用情况:
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list | find "="

echo.
echo 磁盘空间:
wmic logicaldisk get size,freespace,caption | findstr "C:"

echo.
echo 7. Python环境检查...
python --version 2>nul
if %errorLevel% equ 0 (
    echo Python已安装
    python -c "import flask; print('Flask已安装')" 2>nul || echo 需要安装Flask: pip install flask
    python -c "import requests; print('Requests已安装')" 2>nul || echo 需要安装Requests: pip install requests
) else (
    echo ⚠️  未安装Python，请先安装Python 3.7-3.9版本
    echo 下载地址: https://www.python.org/downloads/windows/
)

echo.
echo 8. 创建监控脚本...
(
echo @echo off
echo :check
echo tasklist /fi "imagename eq python.exe" | find "minimal_server_proxy.py" >nul
echo if %%errorlevel%% equ 0 (
echo     echo 服务运行正常 - %%date%% %%time%%
echo ) else (
echo     echo 服务异常，正在重启...
echo     start "" /min python "%~dp0minimal_server_proxy.py"
echo )
echo timeout /t 60 /nobreak >nul
echo goto check
) > monitor_service.bat

echo.
echo ========================================
echo 优化完成！
echo ========================================
echo.
echo 📊 系统建议:
echo - 当前配置适合轻量级API服务
echo - 建议监控内存使用率，保持在80%%以下
echo - 定期重启服务释放内存
echo - 考虑升级到更新版本的Windows Server
echo.
echo 🚀 启动服务:
echo - 手动启动: python minimal_server_proxy.py
echo - 后台启动: start_api_service.bat
echo - 监控服务: monitor_service.bat
echo.
echo 🔧 其他服务启动脚本:
echo - SSL配置: simple_ssl_setup.bat
echo.
echo 健康检查: http://localhost:5000/health

pause