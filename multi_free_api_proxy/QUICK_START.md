# 快速开始指南

## 🚀 5分钟快速启动

### 1. 验证环境

```bash
# 检查 Python 版本
python --version  # 需要 3.7+

# 检查依赖
pip list | grep -E "flask|requests|watchdog"
```

### 2. 启动服务

```bash
# 进入项目目录
cd multi_free_api_proxy

# 启动优化版本
python multi_free_api_proxy_v3_optimized.py
```

### 3. 验证服务

```bash
# 新开一个终端，测试服务
curl http://localhost:5000/health
# 应返回: {"status": "ok"}
```

## 📊 常用命令

### 查看服务状态

```bash
# 健康检查
curl http://localhost:5000/health

# 上游 API 状态
curl http://localhost:5000/health/upstream

# 并发状态
curl http://localhost:5000/debug/concurrency
```

### 测试聊天功能

```bash
# 发送聊天请求
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    "max_tokens": 200
  }'
```

### 管理 API

```bash
# 获取所有 API 权重
curl http://localhost:5000/debug/api/weight

# 设置 API 权重
curl -X POST http://localhost:5000/debug/api/weight \
  -H "Content-Type: application/json" \
  -d '{"api_name": "free1", "weight": 50}'

# 启用 API
curl -X POST http://localhost:5000/debug/api/enable \
  -H "Content-Type: application/json" \
  -d '{"api_name": "free1"}'

# 停用 API
curl -X POST http://localhost:5000/debug/api/disable \
  -H "Content-Type: application/json" \
  -d '{"api_name": "free1"}'

# 重置权重
curl -X POST http://localhost:5000/debug/api/weight/reset \
  -H "Content-Type: application/json"
```

## 🎨 访问调试面板

打开浏览器访问：
```
http://localhost:5000/debug
```

### 调试面板功能

| 标签页 | 功能 |
|--------|------|
| **统计信息** | 查看调用统计、错误信息、自动刷新 |
| **API状态** | 查看所有 API 的可用性和成功率 |
| **测试聊天** | 直接测试聊天功能 |
| **API管理** | 管理 API 权重、启用/停用 |

## ⚙️ 配置修改

### 修改并发数

编辑 `.env` 文件：
```bash
MAX_CONCURRENT_REQUESTS=10
```

### 修改超时时间

编辑 `config.py`：
```python
class Config:
    TIMEOUT_BASE = 60      # 基础超时时间
    TIMEOUT_RETRY = 90     # 重试超时时间
```

### 启用调试模式

创建 `DEBUG_MODE.txt` 文件：
```bash
touch DEBUG_MODE.txt
```

## 📝 常见问题

### Q: 服务无法启动？

**A:** 检查以下几点：

1. 端口是否被占用
   ```bash
   netstat -an | grep 5000
   ```

2. 依赖是否已安装
   ```bash
   pip install flask requests watchdog
   ```

3. 配置文件是否正确
   ```bash
   cat .env
   ```

### Q: 调试面板无法访问？

**A:** 需要启用调试模式：

```bash
# 创建 DEBUG_MODE.txt 文件
touch DEBUG_MODE.txt

# 重启服务
```

### Q: API 请求失败？

**A:** 检查以下几点：

1. API 密钥是否正确配置
   ```bash
   cat .env | grep API_KEY
   ```

2. 上游 API 是否可用
   ```bash
   curl http://localhost:5000/health/upstream
   ```

3. 查看错误日志
   ```bash
   tail -f daemon.log
   ```

### Q: 如何切换回原始版本？

**A:** 使用备份文件恢复：

```bash
# 停止当前服务
# Ctrl+C

# 恢复原始文件
cp multi_free_api_proxy_v3.py.backup multi_free_api_proxy_v3.py

# 重启服务
python multi_free_api_proxy_v3.py
```

## 🔍 调试技巧

### 查看实时日志

```bash
# 查看最后 20 行日志
tail -20 daemon.log

# 实时查看日志
tail -f daemon.log

# 搜索特定错误
grep "ERROR" daemon.log
```

### 测试 API 连接

```bash
# 测试单个 API
curl -X POST http://free1-api.example.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'
```

### 监控并发请求

```bash
# 查看当前并发数
curl http://localhost:5000/debug/concurrency | jq '.active_requests'

# 持续监控
watch -n 1 'curl -s http://localhost:5000/debug/concurrency | jq ".active_requests"'
```

## 📚 更多资源

- 详细优化指南：[OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- 迁移检查清单：[MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md)
- 原始 README：[../README.md](../README.md)

## 🆘 获取帮助

如遇到问题，请：

1. 查看日志文件：`daemon.log`
2. 访问调试面板：`http://localhost:5000/debug`
3. 检查配置文件：`config.py` 和 `.env`
4. 查看文档：`OPTIMIZATION_GUIDE.md`

## ✨ 下一步

- [ ] 完成迁移检查清单
- [ ] 运行性能测试
- [ ] 配置监控告警
- [ ] 更新团队文档
