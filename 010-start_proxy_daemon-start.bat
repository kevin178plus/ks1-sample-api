@echo off
chcp 65001 >nul 2>&1
title ks1-simple-api Daemon

cd /d "%~dp0"

echo ========================================
echo   ks1-simple-api Daemon
echo ========================================
echo.

python daemon.py start
