@echo off
setlocal enabledelayedexpansion

title ks1-multi-free-api-v3

cd /d "%~dp0"

echo ============================================
echo      ��Free API�������������ű� (V3)
echo ============================================
echo.

REM ����Ĭ�϶˿�
set PORT=5000

REM ����Ƿ��������Զ���˿�
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
