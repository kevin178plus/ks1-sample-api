# 🏭 生产环境部署场景

**适用场景：** 生产服务器、企业级部署、高安全要求

## 📁 文件说明

### 安全部署文件
- **`secure_api_proxy.py`** - 企业级安全代理服务
  - IP白名单访问控制
  - Token身份认证
  - 请求频率限制
  - 完整日志记录
  - 错误处理和超时控制

- **`install_service.bat`** - Windows服务安装脚本
  - 自动安装为Windows服务
  - 服务自启动配置
  - 防火墙规则设置
  - 日志轮转支持

- **`env.production.example`** - 生产环境配置模板
  - 安全参数配置
  - 性能优化设置
  - 监控配置选项

- **`SECURITY_GUIDE.md`** - 详细安全部署指南
  - 完整的部署步骤
  - 安全配置说明
  - 监控和维护指南

- **`setup_ssl_free.bat`** - Let's Encrypt免费SSL证书
  - 自动证书申请和续期
  - Nginx配置生成
  - 自动续期任务设置

## 🚀 生产部署

### 1. 环境准备
```bash
# 复制生产配置
cp env.production.example .env.production

# 编辑配置文件
# 设置OPENROUTER_API_KEY、ALLOWED_IPS、SECRET_TOKEN等
```

### 2. 安装为Windows服务
```bash
# 右键管理员运行
install_service.bat

# 启动服务
net start SecureAPIProxy
```

### 3. SSL证书配置
```bash
# 运行SSL配置脚本
setup_ssl_free.bat

# 配置Nginx（生成nginx配置文件）
# 重启Nginx服务
```

## 🛡️ 安全配置

### 多层防护机制

#### 1. 网络层安全
- **IP白名单** - 只允许特定IP访问
- **防火墙规则** - 只开放必要端口
- **Nginx反向代理** - 隐藏真实服务地址
- **SSL终端** - HTTPS加密传输

#### 2. 应用层安全
- **Token认证** - Bearer Token验证
- **频率限制** - 防止API滥用
- **输入验证** - 参数校验和过滤
- **错误处理** - 安全的错误响应

#### 3. 数据安全
- **密钥管理** - 环境变量存储
- **日志脱敏** - 敏感信息过滤
- **缓存控制** - 生产环境禁用调试缓存
- **访问审计** - 完整的访问日志

### 配置示例
```bash
# .env.production
OPENROUTER_API_KEY=sk-or-v1-your-production-key
ALLOWED_IPS=127.0.0.1,192.168.1.100,10.0.0.50
SECRET_TOKEN=MySecureToken123456
ENABLE_RATE_LIMIT=true
MAX_REQUESTS_PER_HOUR=100
HOST=0.0.0.0
PORT=5000
```

## 📊 监控和日志

### 服务管理
```bash
# 查看服务状态
sc query SecureAPIProxy

# 查看日志
type api_proxy.log

# 实时监控
tail -f api_proxy.log

# 重启服务
net stop SecureAPIProxy && net start SecureAPIProxy
```

### 监控接口
```bash
# 管理统计接口
curl -H "Authorization: Bearer MySecureToken123456" \
     https://your-domain.com/admin/stats

# 健康检查
curl https://your-domain.com/health
```

### 日志格式
```
2026-02-14 14:30:22 - flask - INFO - Chat completion request from 192.168.1.100, message_id: a1b2c3d4
2026-02-14 14:30:25 - flask - INFO - Chat completion completed for message_id: a1b2c3d4
2026-02-14 14:30:30 - flask - WARNING - Rate limit exceeded for 192.168.1.200
```

## 🎯 性能优化

### 线程配置
```python
# secure_api_proxy.py中的线程设置
app.run(host=host, port=port, debug=False, threaded=True)
```

### 超时控制
```python
# 请求超时设置
response = requests.post(
    OPENROUTER_API_URL, 
    json=openrouter_payload, 
    headers=headers,
    timeout=30  # 30秒超时
)
```

### 连接池优化
```python
# 在生产环境中可配置连接池
session = requests.Session()
adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount('https://', adapter)
```

## 🔧 运维管理

### 定期维护任务
```bash
# 清理日志（每周）
logrotate -f /path/to/logrotate.conf

# 检查证书状态（每日）
certbot certificates

# 监控服务状态（每小时）
schtasks /query /tn "API Proxy Health Check"
```

### 备份策略
- **配置文件** - 定期备份.env.production
- **日志文件** - 归档历史日志
- **证书文件** - 备份SSL证书和私钥
- **系统配置** - 备份Nginx和防火墙配置

## 🚨 故障处理

### 常见问题诊断

#### 1. 服务启动失败
```bash
# 检查Python环境
python --version

# 检查依赖
python -c "import flask, requests, watchdog"

# 查看详细错误
type api_proxy.log
```

#### 2. 访问被拒绝
```bash
# 检查IP白名单
# 确认ALLOWED_IPS配置

# 检查Token认证
# 确认Authorization header格式

# 检查频率限制
curl -H "Authorization: Bearer YourToken" \
     https://your-domain.com/admin/stats
```

#### 3. SSL证书问题
```bash
# 检查证书状态
certbot certificates

# 手动续期
certbot renew --dry-run

# 检查Nginx配置
nginx -t
```

### 应急响应
```bash
# 快速重启服务
net stop SecureAPIProxy && net start SecureAPIProxy

# 临时禁用安全限制（紧急情况）
# 修改.env.production，移除IP白名单和Token验证

# 回滚配置
# 使用备份的配置文件替换当前配置
```

## 📋 部署检查清单

### 部署前检查
- [ ] 确认服务器规格（内存4GB+，CPU2核+）
- [ ] 配置域名和DNS解析
- [ ] 准备SSL证书（推荐Let's Encrypt）
- [ ] 设置防火墙规则
- [ ] 准备监控和告警

### 部署后验证
- [ ] 服务正常启动
- [ ] HTTPS访问正常
- [ ] API功能测试通过
- [ ] 日志记录正常
- [ ] 监控指标正常

这个场景适合需要高安全性和稳定性的生产环境。