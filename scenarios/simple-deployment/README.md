# 🚀 简单部署场景

**适用场景：** 快速部署、内网访问、最小配置

## 📁 文件说明

### 简化部署文件
- **`simple_server_proxy.py`** - 简化版API代理服务
  - 最小化配置，易于部署
  - 移除复杂的安全机制
  - 保留核心API转发功能
  - 支持外网访问（0.0.0.0绑定）

## 🎯 使用场景

### 适合以下情况：
- ✅ 内网环境，多台服务器间调用
- ✅ 信任网络，不需要复杂认证
- ✅ 快速验证和测试
- ✅ 个人项目或小团队使用
- ✅ 临时API服务需求

### 不适合以下情况：
- ❌ 公网暴露服务
- ❌ 高安全性要求
- ❌ 需要详细审计和监控
- ❌ 大规模生产环境

## 🚀 快速部署

### 1. 准备环境
```bash
# 确保Python已安装（3.7+）
python --version

# 安装必要依赖
pip install flask requests
```

### 2. 配置环境
```bash
# 创建.env文件
echo OPENROUTER_API_KEY=your-key-here > .env

# 可选：设置Referer
echo HTTP_REFERER=http://your-server.com:5000 >> .env
```

### 3. 启动服务
```bash
# 直接启动
python simple_server_proxy.py

# 后台启动（Linux/Mac）
nohup python simple_server_proxy.py > proxy.log 2>&1 &

# Windows后台启动
start /B python simple_server_proxy.py
```

## 📡 服务访问

### API端点
- **服务地址**: `http://你的服务器IP:5000`
- **聊天API**: `http://你的服务器IP:5000/v1/chat/completions`
- **模型列表**: `http://你的服务器IP:5000/v1/models`
- **健康检查**: `http://你的服务器IP:5000/health`

### 调用示例
```bash
# cURL调用
curl -X POST http://192.168.1.100:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好！"}]
  }'

# Python调用
import requests
response = requests.post(
    "http://192.168.1.100:5000/v1/chat/completions",
    json={"messages": [{"role": "user", "content": "你好！"}]}
)
print(response.json())
```

## 🔧 简化配置

### 最小.env配置
```bash
# 必需：OpenRouter API密钥
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# 可选：Referer设置
HTTP_REFERER=http://your-server.com:5000

# 可选：自定义端口（修改代码中的port值）
# PORT=8080
```

### 端口配置
如需修改端口，编辑`simple_server_proxy.py`文件最后一行：
```python
app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
```

## 🛡️ 基础安全

### 防火墙配置
```bash
# Windows防火墙
netsh advfirewall firewall add rule name="API Proxy" dir=in action=allow protocol=TCP localport=5000

# Linux防火墙（iptables）
iptables -A INPUT -p tcp --dport 5000 -j ACCEPT

# 云服务商安全组
# 开放5000端口，限制来源IP（推荐）
```

### 内网访问控制
如果只允许特定IP访问，可以在代码中添加简单过滤：
```python
@app.before_request
def limit_remote_addr():
    allowed_ips = ['192.168.1.100', '10.0.0.50', '127.0.0.1']
    if request.remote_addr not in allowed_ips:
        return jsonify({"error": "Access denied"}), 403
```

## 📊 基础监控

### 健康检查
```bash
# 检查服务状态
curl http://localhost:5000/health

# 预期响应
{
    "status": "ok",
    "server": "Simple API Proxy"
}
```

### 进程监控
```bash
# Windows
tasklist | find python.exe

# Linux/Mac
ps aux | grep simple_server_proxy
```

## 🔧 运维脚本

### 启动脚本（start_simple.bat）
```batch
@echo off
cd /d "%~dp0"
echo 启动简化版API代理...
python simple_server_proxy.py
pause
```

### 监控脚本（monitor_simple.sh）
```bash
#!/bin/bash
while true; do
    if ! pgrep -f "simple_server_proxy.py" > /dev/null; then
        echo "服务异常，正在重启..."
        python simple_server_proxy.py &
    fi
    sleep 60
done
```

## 🚨 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 查看端口占用（Windows）
netstat -ano | findstr :5000

# 查看端口占用（Linux）
lsof -i :5000

# 解决方案：修改端口号或停止占用进程
```

#### 2. 连接被拒绝
```bash
# 检查服务是否启动
curl http://localhost:5000/health

# 检查防火墙设置
# 确认5000端口已开放
```

#### 3. API调用失败
```bash
# 检查API密钥配置
# 确认.env文件中的OPENROUTER_API_KEY正确

# 检查网络连接
ping openrouter.ai
```

#### 4. 内存使用过高
```bash
# 重启服务释放内存
# 考虑使用win2012-server场景的最小化版本
```

## 📈 性能考虑

### 资源使用
- **内存占用**: ~30-80MB（取决于并发数）
- **CPU使用**: 低负载，适合单核CPU
- **网络带宽**: 根据API调用量决定

### 优化建议
- 使用SSD硬盘提高I/O性能
- 配置足够的内存避免频繁交换
- 监控网络流量，防止带宽不足

## 🔄 升级路径

当简单部署无法满足需求时，可以考虑升级到：

1. **需要更多安全功能** → 升级到 `production` 场景
2. **低配服务器** → 使用 `win2012-server` 场景
3. **需要调试功能** → 使用 `development` 场景

## 📝 部署检查清单

- [ ] Python环境已安装（3.7+）
- [ ] Flask和Requests依赖已安装
- [ ] .env文件已配置API密钥
- [ ] 防火墙规则已配置
- [ ] 服务能正常启动
- [ ] 健康检查接口正常响应
- [ ] API调用测试通过

这个场景适合需要快速部署、配置简单的内网环境。