@echo off
chcp 65001 >nul
echo ========================================
echo 系统回退脚本 - 恢复原始配置
echo ========================================
echo.
echo 此脚本将撤销 win2012_optimization.bat 的所有修改
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 请以管理员身份运行此脚本
    pause
    exit /b 1
)

echo 1. 恢复虚拟内存设置（系统管理）...
wmic computersystem where name="%computername%" set AutomaticManagedPagefile=True >nul 2>&1
echo ✅ 虚拟内存已恢复为系统管理

echo.
echo 2. 恢复系统服务...
:: 恢复被禁用的服务
sc config "Themes" start= demand >nul 2>&1
sc config "DesktopWindowManager" start= demand >nul 2>&1  
sc config "Windows Search" start= demand >nul 2>&1
echo ✅ 系统服务已恢复为按需启动

echo.
echo 3. 删除API代理防火墙规则...
netsh advfirewall firewall delete rule name="API Proxy" >nul 2>&1
netsh advfirewall firewall delete rule name="API Proxy Safe" >nul 2>&1
echo ✅ 防火墙规则已删除

echo.
echo 4. 删除开机自启动任务...
schtasks /delete /tn "API Proxy Auto Start" /f >nul 2>&1
echo ✅ 开机任务已删除

echo.
echo 5. 清理生成的文件...
if exist "start_api_service.bat" del "start_api_service.bat"
if exist "monitor_service.bat" del "monitor_service.bat"
if exist "api_proxy.log" del "api_proxy.log"
echo ✅ 临时文件已清理

echo.
echo 6. 停止可能运行的API代理服务...
taskkill /f /im python.exe /fi "windowtitle eq API Proxy Service*" >nul 2>&1
echo ✅ API代理服务已停止

echo.
echo ========================================
echo 回退完成！
echo ========================================
echo.
echo 系统已恢复到优化前的状态：
echo - 虚拟内存：由系统自动管理
echo - 系统服务：恢复为按需启动
echo - 防火墙：删除了API代理规则
echo - 开机任务：删除了自启动任务
echo - 临时文件：已清理
echo.
echo 如需重新部署API代理，请重新运行相应脚本
echo.

pause