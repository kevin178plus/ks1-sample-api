@echo off

title ks1-multi-free-api-v3

cd /d "%~dp0"

echo ============================================
echo      多Free API代理服务启动脚本 (V3)
echo ============================================
echo.

REM 从 .env 文件加载环境变量（包括 PORT）
if exist .env (
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        set %%a=%%b
    )
)

REM 如果 .env 中没有配置 PORT，使用命令行参数或默认值
if "%PORT%"=="" (
    set PORT=5000
)

REM 检查是否设置了命令行参数（优先级最高）
if not "%1"=="" (
    set PORT=%1
)

echo [����] �˿�: %PORT%
echo.

echo Checking dependencies...
pip show watchdog >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependency: watchdog
    pip install watchdog
)
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependency: flask
    pip install flask
)
pip show requests >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependency: requests
    pip install requests
)
echo.

REM ������ģʽ
if exist DEBUG_MODE.txt (
    echo [����] ����ģʽ������
    echo [����] �ɷ��� http://localhost:%PORT%/debug �鿴�������
    echo.
) else (
    echo [����] ����ģʽδ���� ^(���� DEBUG_MODE.txt �ļ�������^)
    echo.
)

echo Dependency check complete, starting service...
echo.
echo [����] ����������Free API�������� (V3)...
echo.

REM ��������
python multi_free_api_proxy\multi_free_api_proxy_v3.py

echo.
echo ������ֹͣ
pause
