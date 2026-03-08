@echo off
chcp 65001 >nul
echo ========================================
echo 文档生成器 - 快速启动
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [信息] 检查依赖...
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 安装 requests 库...
    pip install requests
)

echo.
echo ========================================
echo 文档生成器已就绪
echo ========================================
echo.
echo 使用方法:
echo 1. 修改 doc_generator.py 中的 PHP_API_URL
echo 2. 运行: python doc_generator.py
echo.
echo 或者导入使用:
echo   from doc_generator import DocGenerator
echo   generator = DocGenerator("http://your-server.com/api")
echo   result = generator.upload_and_get_link(title, content)
echo.
pause