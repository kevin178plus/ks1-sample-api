# API 代理服务 (Go 版本)

高性能、低内存占用的 API 代理服务，使用 Go 语言重写，支持多上游负载均衡、失效转移、限额统计和动态权重调整。

## 📋 目录

- [特性](#特性)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [上游配置](#上游配置)
- [API 端点](#api-端点)
- [调试模式](#调试模式)
- [部署指南](#部署指南)
- [性能优化](#性能优化)

## ✨ 特性

### 核心功能

- ✅ **多上游负载均衡** - 支持权重轮询和随机选择
- ✅ **失效转移** - 自动重试失败请求，切换到可用上游
- ✅ **健康检查** - 定期检查上游可用性（默认12小时）
- ✅ **限额统计** - 按调用次数统计，支持小时/日/月限额
- ✅ **动态权重调整** - 达到阈值自动降权重，成功后自动恢复
- ✅ **Webhook 通知** - 限额接近时自动发送通知
- ✅ **多模型支持** - 单个上游支持多个模型，支持模型权重选择
- ✅ **API Key 认证** - 支持白名单验证和按密钥限额统计
- ✅ **限流中间件** - 基于令牌桶算法的请求限流
- ✅ **调试模式** - 完整的流量日志和 Web 调试面板
- ✅ **优雅重启** - 配置文件变化时自动优雅重启（< 3秒）

### 与 Python 版本的差异

| 功能 | Python 版本 | Go 版本 | 说明 |
|------|------------|---------|------|
| 限额统计 | 请求次数 | 请求次数 | 统计方式相同 |
| 健康检查 | 仅启动时 | 可配置周期（默认12小时） | Go 版本支持定期检查 |
| 配置热加载 | 重启 | 优雅重启（< 3秒） | Go 版本采用重启策略，内存效率更高 |
| API Key 白名单 | 无 | 有 | Go 版本支持白名单验证 |
| 按 API Key 统计 | 无 | 有 | Go 版本支持按密钥限额统计 |
| 多模型权重 | 有 | 有 | 功能相同 |

## 🏗️ 架构设计

### 目录结构

```
api-proxy-go/
├── main.go                      # 主入口
├── config/
│   ├── config.go               # 配置加载
│   └── types.go                # 配置类型定义
├── upstream/
│   ├── upstream.go             # 上游管理
│   ├── selector.go             # 负载均衡选择器
│   ├── health.go               # 健康检查
│   └── models.go               # 多模型支持
├── stats/
│   ├── stats.go                # 限额统计
│   ├── key_stats.go            # API Key 统计
│   └── storage.go              # 统计数据持久化
├── proxy/
│   ├── proxy.go                # 反向代理核心
│   └── failover.go             # 失效转移
├── middleware/
│   ├── auth.go                 # API Key 验证
│   ├── rate_limit.go           # 限流
│   └── logger.go               # 请求日志
├── logger/
│   ├── logger.go               # 结构化日志
│   └── traffic.go              # 流量日志
├── models/
│   └── models.go               # 数据模型
├── web/
│   └── debug.go                # 调试页面
└── config.yaml                 # 主配置文件
```

### 核心设计决策

#### 1. 内存优化

- **sync.Pool** 复用缓冲区，减少内存分配
- **sync.Map** 或带锁的 map 管理共享状态
- 避免在热路径中创建临时对象
- 使用值类型减少指针嵌套

#### 2. 配置热加载

采用**优雅重启**策略：
- 监听配置文件变化
- 触发优雅关闭（等待正在处理的请求完成）
- 新进程启动（< 3秒）

优势：
- 内存完全释放，避免潜在的内存泄漏
- 配置简单，无需复杂的原子操作
- 重启时间 < 3秒，对用户体验影响小

#### 3. 限额统计

- 统计**调用次数**（不是 token 数）
- 支持**按上游统计**和**按 API Key 统计**
- 达到警告阈值（80%）触发 webhook 通知
- 达到严重阈值（95%）自动降权重
- 新周期自动重置用量和恢复原始权重

#### 4. 多模型支持

- 每个上游支持多个模型
- 支持模型权重随机选择
- 响应格式可配置（兼容不同 API）

## 🚀 快速开始

### 前置要求

- Go 1.21+
- Windows Server 2012 R2 或更高版本

### 编译

```bash
# 克隆项目
cd D:\ks_ws\git-root\ks1-simple-api\api-proxy-go

# 下载依赖
go mod download

# 编译 Windows 64位可执行文件
set GOOS=windows
set GOARCH=amd64
go build -ldflags="-s -w" -o api-proxy.exe

# 或使用 PowerShell
$env:GOOS="windows"
$env:GOARCH="amd64"
go build -ldflags="-s -w" -o api-proxy.exe
```

### 运行

```bash
# 控制台运行
api-proxy.exe -config config.yaml

# 查看帮助
api-proxy.exe -h
```

### 测试

```bash
# 测试健康检查
curl http://localhost:5000/health

# 测试聊天完成
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## ⚙️ 配置说明

### 主配置文件 (config.yaml)

```yaml
# 监听地址
listen: ":5000"

# 上游配置
upstreams:
  root_dir: "./upstreams"  # 上游配置根目录

# 认证配置
auth:
  enabled: false          # 是否启用认证
  keys: []                # API Key 白名单，为空则允许所有
  key_limit: false        # 是否启用按密钥限额统计
  default_limit: 1000     # 默认限额（调用次数）

# 限流配置
rate_limit:
  enabled: false                  # 是否启用限流
  requests_per_second: 10         # 每秒请求数限制

# 调试配置
debug:
  enabled: false            # 是否启用调试模式
  cache_dir: "./cache"      # 缓存目录
  traffic_log:
    enabled: false          # 是否启用流量日志
    path: "./logs/traffic.json"
    max_size_mb: 100
    max_backups: 3
    compress: true
    buffer_size: 1000
    record_body: true
    max_body_bytes: 1024

# 健康检查配置
health_check:
  enabled: true             # 是否启用健康检查
  interval: 12h             # 检查间隔，默认 12 小时
  timeout: 30s              # 检查超时时间
  max_failures: 3           # 最大连续失败次数

# 权重配置
weight:
  special_threshold: 100    # 特别权重阈值，>100 次必然选中
  min_auto_decrease: 50     # 自动减少权重的下限
```

### 上游配置文件 (upstreams/{name}/config.yaml)

```yaml
name: "API 名称"
address: "https://api.example.com"
api_key: "sk-xxxx"
enabled: true
default_weight: 10

# 限额配置
limit:
  hourly: 1000
  daily: 5000
  monthly: 100000

# 阈值配置
thresholds:
  warning: 80
  critical: 95

# Webhook 通知
webhook: "http://monitor/alert"

# 代理配置
use_proxy: false

# 模型配置
model: "gpt-3.5-turbo"
available_models:
  - "gpt-3.5-turbo"
  - "gpt-4o-mini"
use_weighted_model: true

# 响应格式配置
response_format:
  content_fields: ["content"]
  merge_fields: false
  use_reasoning_as_fallback: false

# 最大 token 数
max_tokens: 2000
```

## 🔌 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | 聊天完成（兼容 OpenAI） |
| `/v1/models` | GET | 列出可用模型 |
| `/health` | GET | 健康检查 |
| `/debug` | GET | 调试面板（需启用调试模式） |
| `/debug/stats` | GET | 统计信息 JSON（需启用调试模式） |
| `/debug/apis` | GET | API 状态（需启用调试模式） |
| `/debug/concurrency` | GET | 并发状态（需启用调试模式） |

## 🐛 调试模式

### 启用调试模式

编辑 `config.yaml`：

```yaml
debug:
  enabled: true
  traffic_log:
    enabled: true
```

### 访问调试面板

打开浏览器访问：`http://localhost:5000/debug`

调试面板包含：
- 统计信息（总调用次数、成功/失败/超时次数）
- API 状态（可用性、权重、连续失败次数）
- 自动刷新（每30秒）

### 流量日志

启用流量日志后，所有请求和响应会记录到文件：
```
./logs/traffic.json
```

日志格式：
```json
{
  "timestamp": "2026-03-03T12:00:00Z",
  "request_id": "abc12345",
  "type": "REQUEST",
  "upstream": "api1",
  "data": {
    "method": "POST",
    "path": "/v1/chat/completions",
    "headers": {...},
    "body": "..."
  }
}
```

## 📦 部署指南

> **注意**: Go 版本不提供 Windows 服务支持。如需后台运行，请使用任务计划程序或第三方工具（如 NSSM）。

### 防火墙配置

```powershell
# 允许端口 5000
New-NetFirewallRule -DisplayName "API Proxy" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

### 日志管理

日志文件位置：
- 统计日志：`{cache_dir}/STATS_YYYYMMDD.json`
- API Key 统计：`{cache_dir}/KEY_STATS_YYYYMMDD.json`
- 流量日志：`{traffic_log.path}`

## ⚡ 性能优化

### 内存优化

- **sync.Pool** 复用缓冲区
- **sync.Map** 管理共享状态
- 避免在热路径中创建临时对象
- 使用值类型减少指针嵌套

### 并发优化

- **goroutine** 处理并发请求
- **连接池** 复用 HTTP 连接
- **限流中间件** 防止过载

### 配置优化

- 优雅重启时间 < 3秒
- 健康检查间隔可配置（默认12小时）
- 流量日志异步写入

## 🔍 监控和维护

### 健康检查

```bash
curl http://localhost:5000/health
```

### 查看统计

```bash
curl http://localhost:5000/debug/stats
```

### 查看 API 状态

```bash
curl http://localhost:5000/debug/apis
```

## 🆘 故障排除

### 服务无法启动

1. 检查端口是否被占用
2. 检查配置文件语法
3. 查看日志输出

### API 不可用

1. 检查 API Key 是否正确
2. 检查上游配置是否正确
3. 查看健康检查日志
4. 访问调试面板查看状态

### 请求失败

1. 检查上游是否可用
2. 查看失效转移日志
3. 检查限额是否达到

### 配置重载失败

1. 检查配置文件权限
2. 确认配置文件语法正确
3. 查看日志输出

## 📝 功能说明

### 不支持的功能

- ❌ **SDK 模式** - Go 版本不开发 SDK 模式，仅支持 HTTP 代理模式
- ❌ **Windows 服务支持** - Go 版本不提供原生 Windows 服务支持，建议使用任务计划程序或 NSSM 等第三方工具

### 未来计划

- [ ] 添加 Prometheus 指标
- [ ] 添加更多测试用例
- [ ] 优化流量日志性能
- [ ] 支持更多上游类型

## 📄 许可证

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！