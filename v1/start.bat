@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================
echo        Evidence Package Collector
echo ============================================
echo.

"D:\phpstudy_pro\Extensions\php\php7.4.3nts\php.exe" -S localhost:12680 kuaecloud-api.php

echo.
echo Done!
pause
