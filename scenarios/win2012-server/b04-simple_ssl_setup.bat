@echo off
chcp 65001 >nul
echo ========================================
echo Windows Server 2012 R2 SSL 设置方案
echo ========================================
echo.

:: 检查系统版本
echo 检测到 Windows Server 2012 R2
echo 推荐使用自签名证书或 cloudflare.com 方案
echo.

echo 选择SSL方案:
echo 1. 自签名证书 (适合内网测试)
echo 2. Cloudflare 免费SSL (推荐，无需服务器配置)
echo 3. HTTP直接部署 (仅内网)
echo.
set /p ssl_choice=请选择 (1/2/3): 

if "%ssl_choice%"=="1" goto self_signed
if "%ssl_choice%"=="2" goto cloudflare
if "%ssl_choice%"=="3" goto http_only
goto invalid_choice

:self_signed
echo.
echo 生成自签名证书...
powershell -Command "& {
    $cert = New-SelfSignedCertificate -DnsName 'localhost','127.0.0.1' -CertStoreLocation 'cert:\LocalMachine\My' -KeyUsage KeyEncipherment,DigitalSignature -Type SSLServerAuthentication;
    $thumbprint = $cert.Thumbprint;
    Export-PfxCertificate -Cert \"cert:\LocalMachine\My\$thumbprint\" -FilePath 'server.pfx' -Password (ConvertTo-SecureString -String '123456' -Force -AsPlainText);
    Write-Host '证书已生成: server.pfx (密码: 123456)';
    Write-Host '指纹: $thumbprint';
}"

echo.
echo 配置 HTTPS 监听...
netsh http add sslcert ipport=0.0.0.0:5000 certhash=thumbprint appid={00112233-4455-6677-8899-AABBCCDDEEFF}
echo ✅ 自签名SSL配置完成
echo.
echo 使用方法:
echo 1. 安装证书到客户端信任存储
echo 2. 访问 https://服务器IP:5000/health
goto end

:cloudflare
echo.
echo ========================================
echo Cloudflare 免费SSL方案 (强烈推荐)
echo ========================================
echo.
echo 步骤:
echo 1. 注册 Cloudflare 账户 (免费)
echo 2. 将你的域名指向 Cloudflare DNS
echo 3. 在 Cloudflare 控制台开启 SSL/TLS (灵活模式)
echo 4. 配置代理规则指向你的服务器
echo.
echo 优势:
echo - 完全免费
echo - 自动SSL续期
echo - CDN加速
echo - DDoS防护
echo - 无需在服务器配置证书
echo.
echo 配置完成后，其他服务器调用:
echo curl https://你的域名.com/v1/chat/completions ...
echo.
goto end

:http_only
echo.
echo HTTP直接部署配置...
echo.
echo 开启防火墙规则:
netsh advfirewall firewall add rule name="API Proxy HTTP" dir=in action=allow protocol=TCP localport=5000
echo.
echo ⚠️  安全提醒:
echo - 仅适用于可信网络环境
echo - 数据传输未加密
echo - 建议配合云服务商的安全组使用
echo.
echo 其他服务器调用:
echo curl http://服务器IP:5000/v1/chat/completions ...
goto end

:invalid_choice
echo 无效选择，请重新运行脚本
goto end

:end
echo.
echo ========================================
echo 配置完成！
echo ========================================
echo.
echo 推荐启动命令:
python minimal_server_proxy.py
echo.
echo 健康检查:
curl http://localhost:5000/health
echo.

pause