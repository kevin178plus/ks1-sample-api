# BAT 脚本规范

适用于本项目的所有 Windows BAT 脚本。

---

## 1. 必须遵守的规则（Critical）

### 1.1 禁止中文
- **不允许中文注释**
- **不允许中文 echo 输出**
- **不允许中文变量名**
- **只使用英文和 ASCII 字符**

### 1.2 禁止特殊字符
- 避免使用：`@ # $ % ^ & * ( )`（标准批处理语法除外）
- 只使用简单 ASCII 字符
- 禁止 Unicode 字符

### 1.3 路径处理
```bat
@echo off
setlocal enabledelayedexpansion

:: MUST: Always use this at the start
cd /d "%~dp0"

:: Your code here

pause
```

**重要**：
- `cd /d "%~dp0"` - 切换到脚本所在目录，支持盘符切换
- `"%~dp0"` - 获取脚本目录（带引号，支持空格路径）
- `/d` - 允许跨驱动器切换

---

## 2. 标准模板

### 2.1 基础模板
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Your code here

pause
```

### 2.2 带 Python 启动的模板
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Check Python exists
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    exit /b 1
)

:: Run Python script
python run.py

pause
```

### 2.3 带环境变量的模板
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Set environment variables
set API_URL=http://127.0.0.1:12628
set API_KEY=test-key
set LOG_LEVEL=info

:: Check dependencies
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    exit /b 1
)

:: Run application
python main.py --worker

pause
```

### 2.4 停止服务模板
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set APP_NAME=myapp
set PYTHON_EXE=python.exe

:: Try to stop by process name
tasklist /FI "IMAGENAME eq %PYTHON_EXE%" | find /I "%PYTHON_EXE%" >nul
if %errorlevel% equ 0 (
    echo Stopping %APP_NAME%...
    taskkill /F /IM %PYTHON_EXE% >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: Check again
tasklist /FI "IMAGENAME eq %PYTHON_EXE%" | find /I "%PYTHON_EXE%" >nul
if %errorlevel% equ 0 (
    echo WARNING: Some processes still running
) else (
    echo %APP_NAME% stopped successfully
)

pause
```

---

## 3. 环境变量规范

### 3.1 变量定义
```bat
:: GOOD - No spaces around =
set VAR=value

:: BAD - Spaces around =
set VAR = value
```

### 3.2 使用 setlocal
```bat
:: Always use setlocal to avoid polluting parent shell
setlocal enabledelayedexpansion

:: Local variables
set API_KEY=secret-key
set LOG_FILE=app.log

:: Changes won't affect parent shell
endlocal
```

### 3.3 延迟变量扩展
```bat
:: Use enabledelayedexpansion for dynamic variables
setlocal enabledelayedexpansion

set counter=0
for %%i in (1 2 3) do (
    set /a counter+=1
    echo Counter is !counter!  :: Use !var! not %var%
)
```

---

## 4. 错误处理

### 4.1 检查错误级别
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Run command
python script.py

:: Check error level
if %errorlevel% neq 0 (
    echo ERROR: Script failed with code %errorlevel%
    exit /b 1
)

echo Script completed successfully
pause
```

### 4.2 检查依赖
```bat
:: Check Python exists
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8 or higher
    exit /b 1
)

:: Check required module
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: flask module not found
    echo Run: pip install flask
    exit /b 1
)
```

### 4.3 退出码
```bat
:: Success
exit /b 0

:: Generic error
exit /b 1

:: Custom error codes
exit /b 2  :: Configuration error
exit /b 3  :: Dependency error
exit /b 4  :: Runtime error
```

---

## 5. Python 集成

### 5.1 启动 Python 脚本
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Simple launch
python script.py

:: With arguments
python script.py --port 12628 --debug

:: With output redirection
python script.py > output.log 2>&1

:: In background (Windows 10+)
start /B python script.py
```

### 5.2 内联 Python 代码
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Single line
python -c "print('Hello World')"

:: Multi-line with -c
python -c ^
"import sys; ^
print(f'Python version: {sys.version}'); ^
print('Done')"

:: Using triple quotes for Windows paths
python -c ^
"import os; ^
path = r'C:\Program Files\App'; ^
print(os.path.exists(path))"
```

### 5.3 传递参数
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Set variables
set PORT=12628
set HOST=127.0.0.1

:: Pass to Python
python main.py --host !HOST! --port !PORT!

:: Or use environment variables
set APP_PORT=12628
set APP_HOST=127.0.0.1
python main.py
```

---

## 6. 字符串处理

### 6.1 引号处理
```bat
:: Always quote paths with spaces
set FILE_PATH="C:\Program Files\My App\config.txt"

:: Remove quotes if needed
set FILE_PATH=%FILE_PATH:"=%

:: Add quotes
set FILE_PATH="!FILE_PATH!"
```

### 6.2 字符串操作
```bat
:: Substring
set STRING=Hello World
set SUBSTRING=%STRING:~0,5%
echo %SUBSTRING%  :: Output: Hello

:: Replace
set STRING=Hello World
set REPLACED=%STRING:World=Python%
echo %REPLACED%  :: Output: Hello Python

:: Remove extension
set FILENAME=script.py
set BASENAME=%FILENAME:~0,-4%
echo %BASENAME%  :: Output: script
```

---

## 7. 路径操作

### 7.1 获取脚本相关路径
```bat
@echo off
setlocal enabledelayedexpansion

:: Script directory (with drive)
set SCRIPT_DIR=%~dp0

:: Script directory (without drive)
set SCRIPT_PATH=%~p0

:: Script drive
set SCRIPT_DRIVE=%~d0

:: Script full path
set SCRIPT_PATH_FULL=%~f0

:: Script name without extension
set SCRIPT_NAME=%~n0

:: Script extension
set SCRIPT_EXT=%~x0

echo Script dir: %SCRIPT_DIR%
echo Script name: %SCRIPT_NAME%
echo Script ext: %SCRIPT_EXT%
```

### 7.2 构建路径
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Base directory
set BASE_DIR=%~dp0

:: Build path
set CONFIG_DIR=%BASE_DIR%config
set LOG_DIR=%BASE_DIR%logs
set LOG_FILE=%LOG_DIR%\app.log

:: Use quotes for paths with spaces
if not exist "%CONFIG_DIR%" (
    mkdir "%CONFIG_DIR%"
)
```

### 7.3 检查路径存在
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: Check file exists
if exist "config.yaml" (
    echo Config file found
) else (
    echo ERROR: Config file not found
    exit /b 1
)

:: Check directory exists
if exist "logs\" (
    echo Logs directory exists
) else (
    mkdir logs
)
```

---

## 8. 条件和循环

### 8.1 If 语句
```bat
:: Check if variable is defined
if defined VAR_NAME (
    echo VAR_NAME is defined
) else (
    echo VAR_NAME is not defined
)

:: Check if variable equals value
if "%VAR_NAME%"=="value" (
    echo Match
)

:: Check if variable not equals value
if not "%VAR_NAME%"=="value" (
    echo No match
)

:: Check if file exists
if exist "file.txt" (
    echo File exists
)

:: Check if directory exists
if exist "directory\" (
    echo Directory exists
)
```

### 8.2 For 循环
```bat
:: Iterate over files
for %%f in (*.py) do (
    echo Processing: %%f
    python "%%f"
)

:: Iterate over directories
for /d %%d in (*) do (
    echo Directory: %%d
)

:: Iterate with counter
set counter=0
for %%i in (1 2 3 4 5) do (
    set /a counter+=1
    echo Item !counter!
)
```

---

## 9. 注释规范

### 9.1 单行注释
```bat
:: This is a comment
set VAR=value  :: Inline comment
```

### 9.2 块注释
```bat
:: ==========================================
:: This is a block comment
:: It can span multiple lines
:: ==========================================
```

### 9.3 禁止的注释
```bat
:: ❌ WRONG - Chinese comments
:: 这是中文注释

:: ✅ CORRECT - English comments
:: This is English comment
```

---

## 10. 最佳实践

### 10.1 总是使用引号
```bat
:: GOOD - Always quote paths
cd "%~dp0"
python "script with spaces.py"

:: BAD - No quotes
cd %~dp0
python script with spaces.py
```

### 10.2 使用延迟扩展
```bat
:: GOOD - Use enabledelayedexpansion
setlocal enabledelayedexpansion
set counter=0
for %%i in (1 2 3) do (
    set /a counter+=1
    echo !counter!
)

:: BAD - Won't work as expected
set counter=0
for %%i in (1 2 3) do (
    set /a counter+=1
    echo %counter%  :: Will always print 0
)
```

### 10.3 检查错误
```bat
:: GOOD - Check error level
python script.py
if %errorlevel% neq 0 (
    echo ERROR: Script failed
    exit /b 1
)

:: BAD - Don't check errors
python script.py
echo Done  :: May print even if script failed
```

---

## 11. 完整示例

### 11.1 启动脚本（完整版）
```bat
@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: ==========================================
:: Configuration
:: ==========================================
set APP_NAME=myapp
set PYTHON_SCRIPT=run.py
set LOG_FILE=logs\myapp.log
set PID_FILE=myapp.pid

:: ==========================================
:: Check dependencies
:: ==========================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    exit /b 1
)

:: ==========================================
:: Create log directory
:: ==========================================
if not exist "logs" (
    mkdir logs
)

:: ==========================================
:: Check if already running
:: ==========================================
if exist "%PID_FILE%" (
    echo WARNING: PID file exists
    echo Please run stop script first
    exit /b 1
)

:: ==========================================
:: Start application
:: ==========================================
echo Starting %APP_NAME%...
start /B python %PYTHON_SCRIPT% > "%LOG_FILE%" 2>&1

:: Save PID
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV ^| find /I "python.exe"') do (
    set PID=%%i
    echo !PID! > "%PID_FILE%"
)

echo %APP_NAME% started successfully
echo Log file: %LOG_FILE%
echo PID: !PID!

pause
```

---

## 版本信息

- **文档版本**：1.0
- **创建日期**：2026-02-28
- **适用项目**：ks1-simple-api
