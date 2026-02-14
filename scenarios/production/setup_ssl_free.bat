@echo off
chcp 65001 >nul
echo ========================================
echo 免费SSL证书自动续期设置
echo ========================================
echo.

:: 检查是否有域名
set /p domain_name=请输入你的域名 (例如: api.yourdomain.com): 
if "%domain_name%"=="" (
    echo 错误: 必须输入域名
    pause
    exit /b 1
)

echo.
echo 正在安装 Certbot (Let's Encrypt 客户端)...

:: 下载并安装 Certbot
echo 1. 下载 Certbot...
powershell -Command "Invoke-WebRequest -Uri 'https://dl.eff.org/certbot-beta-setup.exe' -OutFile 'certbot-setup.exe'"
if %errorLevel% neq 0 (
    echo 下载失败，尝试使用 Chocolatey 安装...
    where choco >nul 2>&1
    if %errorLevel% neq 0 (
        echo 请先安装 Chocolatey: https://chocolatey.org/install
        pause
        exit /b 1
    )
    choco install certbot
) else (
    echo 运行 Certbot 安装程序...
    certbot-setup.exe /S
)

:: 检查安装
certbot --version >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: Certbot 安装失败
    pause
    exit /b 1
)

echo.
echo 2. 配置防火墙开放 80 和 443 端口...
netsh advfirewall firewall add rule name="Certbot HTTP" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="Certbot HTTPS" dir=in action=allow protocol=TCP localport=443

echo.
echo 3. 生成 SSL 证书...
echo 注意: 你的域名 %domain_name% 必须已指向这台服务器的IP
echo.

:: 创建临时Web目录用于验证
mkdir C:\temp\web >nul 2>&1

:: 生成证书
certbot certonly --standalone --preferred-challenges http -d %domain_name% --email admin@%domain_name% --agree-tos --non-interactive

if %errorLevel% equ 0 (
    echo.
    echo ✅ SSL证书生成成功！
    echo 证书位置: C:\Certbot\live\%domain_name%\fullchain.pem
    echo 私钥位置: C:\Certbot\live\%domain_name%\privkey.pem
    echo.
    
    :: 创建自动续期任务
    echo 4. 设置自动续期...
    schtasks /create /tn "Certbot Auto Renew" /tr "certbot renew --quiet" /sc daily /st 02:00
    
    echo.
    echo 5. 生成 Nginx 配置文件...
    (
        echo server {
        echo     listen 80;
        echo     server_name %domain_name%;
        echo     return 301 https://$server_name$request_uri;
        echo }
        echo.
        echo server {
        echo     listen 443 ssl http2;
        echo     server_name %domain_name%;
        echo.
        echo     ssl_certificate C:/Certbot/live/%domain_name%/fullchain.pem;
        echo     ssl_certificate_key C:/Certbot/live/%domain_name%/privkey.pem;
        echo     ssl_protocols TLSv1.2 TLSv1.3;
        echo     ssl_ciphers HIGH:!aNULL:!MD5;
        echo.
        echo     location / {
        echo         proxy_pass http://127.0.0.1:5000;
        echo         proxy_set_header Host $host;
        echo         proxy_set_header X-Real-IP $remote_addr;
        echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo         proxy_set_header X-Forwarded-Proto $scheme;
        echo         proxy_connect_timeout 30s;
        echo         proxy_send_timeout 30s;
        echo         proxy_read_timeout 30s;
        echo     }
        echo }
    ) > nginx_%domain_name%.conf
    
    echo ✅ Nginx配置已生成: nginx_%domain_name%.conf
    echo 请将此文件内容添加到你的 Nginx 配置中
    echo.
    echo 6. 测试证书续期...
    certbot renew --dry-run
    
    if %errorLevel% equ 0 (
        echo ✅ 自动续期测试成功！
        echo 系统将在每天凌晨2点自动检查并续期证书
    )
    
) else (
    echo ❌ SSL证书生成失败
    echo 请检查:
    echo 1. 域名 %domain_name% 是否正确解析到这台服务器
    echo 2. 80端口是否被占用
    echo 3. 防火墙是否允许80端口访问
)

echo.
echo ========================================
echo 设置完成！
echo ========================================
echo.
echo 使用方法:
echo 1. 启动简化版代理: python simple_server_proxy.py
echo 2. 重启 Nginx: nginx -s reload
echo 3. 访问: https://%domain_name%/health
echo.
echo 检查证书: certbot certificates
echo 手动续期: certbot renew
echo 查看续期任务: schtasks /query /tn "Certbot Auto Renew"
echo.

pause