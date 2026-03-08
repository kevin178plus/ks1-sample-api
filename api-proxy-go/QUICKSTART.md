# 快速开始指南

## 第一步：编译

```bash
cd D:\ks_ws\git-root\ks1-simple-api\api-proxy-go
build.bat
```

## 第二步：配置

编辑 `config.yaml` 文件，根据需要修改配置：

```yaml
# 监听地址
listen: ":5000"

# 上游配置
upstreams:
  root_dir: "./upstreams"

# 启用调试模式（可选）
debug:
  enabled: true
  traffic_log:
    enabled: true
```

## 第三步：添加上游

在 `upstreams/` 目录下创建子目录，每个子目录代表一个上游服务：

```
upstreams/
├── example/
│   └── config.yaml
├── api1/
│   └── config.yaml
└── api2/
    └── config.yaml
```

参考 `upstreams/example/config.yaml` 创建上游配置。

## 第四步：运行

```bash
run.bat
```

## 第五步：测试

```bash
# 测试健康检查
curl http://localhost:5000/health

# 测试聊天完成
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# 访问调试面板（如果启用了调试模式）
# 浏览器打开: http://localhost:5000/debug
```

## 常见问题

### Q: 如何启用 API Key 认证？

A: 编辑 `config.yaml`：

```yaml
auth:
  enabled: true
  keys:
    - "your-api-key-1"
    - "your-api-key-2"
  key_limit: true
  default_limit: 1000
```

### Q: 如何修改健康检查间隔？

A: 编辑 `config.yaml`：

```yaml
health_check:
  enabled: true
  interval: 6h  # 改为 6 小时
```

### Q: 如何配置按密钥限额统计？

A: 编辑 `config.yaml`：

```yaml
auth:
  key_limit: true
  default_limit: 1000  # 每个 API Key 默认限额
```

### Q: 如何查看运行时统计？

A: 访问调试面板：
```
http://localhost:5000/debug
```

或调用 API：
```bash
curl http://localhost:5000/debug/stats
curl http://localhost:5000/debug/apis
```

### Q: 如何优雅重启？

A: 修改 `config.yaml` 后，服务会自动检测并优雅重启（< 3秒）。

## 与 Python 版本的主要差异

1. **配置热加载**：Go 版本采用优雅重启（< 3秒），内存效率更高
2. **健康检查**：支持定期检查（默认12小时），而 Python 版本只在启动时检查
3. **API Key 白名单**：Go 版本支持白名单验证和按密钥限额统计
4. **多模型权重**：功能相同，都支持模型权重随机选择

## 下一步

- 阅读 [README.md](README.md) 了解详细功能
- 查看 [config.yaml](config.yaml) 了解配置选项
- 参考 [upstreams/example/config.yaml](upstreams/example/config.yaml) 了解上游配置
- 访问 [调试面板](http://localhost:5000/debug) 监控运行状态