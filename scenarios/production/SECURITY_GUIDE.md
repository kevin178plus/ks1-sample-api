# 🔒 服务器部署安全指南

## 📋 部署前检查清单

### ✅ 必须配置项
- [ ] 配置 `.env.production` 文件
- [ ] 设置 IP 白名单或 Token 认证
- [ ] 禁用调试模式
- [ ] 配置 Nginx 反向代理 + SSL
- [ ] 设置 Windows 防火墙规则
- [ ] 安装为 Windows 服务

### ⚠️ 可选配置项
- [ ] 启用请求频率限制
- [ ] 配置日志轮转
- [ ] 设置监控告警
- [ ] 配置自动备份

## 🚀 快速部署步骤

### 1. 环境准备
```bash
# 1. 安装依赖
pip install flask requests watchdog

# 2. 创建生产环境配置文件
cp env.production.example .env.production
```

### 2. 配置安全参数
编辑 `.env.production` 文件：
```bash
# API配置
OPENROUTER_API_KEY=sk-or-v1-your-real-key-here

# 安全配置 - 三选一或组合使用
ALLOWED_IPS=127.0.0.1,192.168.1.100,::1
SECRET_TOKEN=your-super-secret-token-here
ENABLE_RATE_LIMIT=true
MAX_REQUESTS_PER_HOUR=50

# 禁用调试模式
# CACHE_DIR=  # 留空
```

### 3. 安装Windows服务
```bash
# 右键以管理员身份运行
install_service.bat
```

### 4. 配置Nginx反向代理
参考下面的Nginx配置示例

## 🛡️ 安全配置详解

### 1. IP白名单（推荐）
```bash
# 只允许特定IP访问
ALLOWED_IPS=127.0.0.1,192.168.1.100,192.168.1.101
```

### 2. Token认证（推荐）
```bash
# 设置访问令牌
SECRET_TOKEN=MySecretToken123456

# 客户端调用时需要添加Header
Authorization: Bearer MySecretToken123456
```

### 3. 频率限制（推荐）
```bash
ENABLE_RATE_LIMIT=true
MAX_REQUESTS_PER_HOUR=100  # 每小时最多100次请求
```

### 4. Nginx SSL配置
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL证书
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # 访问控制（可选）
    allow 192.168.1.0/24;
    deny all;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}

# HTTP跳转HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 🔧 客户端调用示例

### Python（带认证）
```python
import requests

# 方式1: IP白名单
response = requests.post(
    "https://your-domain.com/v1/chat/completions",
    json={"messages": [{"role": "user", "content": "Hello!"}]}
)

# 方式2: Token认证
headers = {
    "Authorization": "Bearer MySecretToken123456",
    "Content-Type": "application/json"
}
response = requests.post(
    "https://your-domain.com/v1/chat/completions",
    headers=headers,
    json={"messages": [{"role": "user", "content": "Hello!"}]}
)
```

### cURL（带认证）
```bash
# Token认证
curl -X POST https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer MySecretToken123456" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## 📊 监控和维护

### 1. 查看服务状态
```bash
# 检查服务状态
sc query SecureAPIProxy

# 查看日志
type api_proxy.log

# 查看实时日志
tail -f api_proxy.log
```

### 2. 服务管理
```bash
# 启动服务
net start SecureAPIProxy

# 停止服务
net stop SecureAPIProxy

# 重启服务
net stop SecureAPIProxy && net start SecureAPIProxy
```

### 3. 监控API访问
访问管理统计接口：
```bash
curl -H "Authorization: Bearer MySecretToken123456" \
     https://your-domain.com/admin/stats
```

## ⚠️ 安全注意事项

### 1. 文件权限
- 确保 `.env.production` 文件只有管理员可读
- 日志文件定期清理，避免磁盘空间不足
- 缓存目录（如果启用）需要适当权限

### 2. 网络安全
- 使用HTTPS，不要在生产环境使用HTTP
- 配置防火墙，只开放必要端口
- 定期更新SSL证书

### 3. API密钥安全
- 定期更换OpenRouter API密钥
- 监控API使用量，防止滥用
- 不要在代码中硬编码API密钥

### 4. 调试模式
- 生产环境必须禁用调试模式
- 不要创建 `DEBUG_MODE.txt` 文件
- 不配置 `CACHE_DIR` 参数

## 🚨 故障处理

### 常见问题及解决方案

1. **服务启动失败**
   - 检查Python环境
   - 查看api_proxy.log日志
   - 确认配置文件格式正确

2. **无法访问API**
   - 检查Nginx配置
   - 确认防火墙规则
   - 验证IP白名单或Token

3. **认证失败**
   - 检查ALLOWED_IPS配置
   - 验证SECRET_TOKEN格式
   - 确认请求Header格式

4. **性能问题**
   - 检查频率限制设置
   - 监控服务器资源使用
   - 查看OpenRouter API状态

## 📞 技术支持

如果遇到问题，请按以下步骤排查：

1. 检查Windows事件日志
2. 查看api_proxy.log文件
3. 验证配置文件格式
4. 测试网络连通性
5. 检查OpenRouter API状态

---

**重要提醒：部署到生产环境前请务必完成所有安全配置！**