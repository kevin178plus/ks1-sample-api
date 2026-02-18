@echo off
chcp 65001 >nul
title API Proxy - Minimal Setup
echo 启动最小化API代理...
echo 服务地址: http://localhost:5000
echo 按 Ctrl+C 停止
echo.
python minimal_server_proxy.py
