# 多免费 API 代理服务

一个轻量级的本地 API 代理服务，让你无需配置复杂的 One API，直接在本机启动一个兼容 OpenAI API 格式的代理，自动使用多个免费 API 模型。

## 🎯 为什么需要这个项目？

- **One API 配置复杂**: One API 功能强大但配置繁琐，仅为了使用免费模型显得过度
- **免费模型经常变化**: 各平台的免费模型列表经常更新，手动维护很麻烦
- **多工具集成困难**: 不同的工具需要配置不同的 API 端点，维护成本高
- **调用次数难以追踪**: 无法直观看到今天用了多少次免费 API
- **单点故障风险**: 单一 API 不可用时，整个服务瘫痪

## ✨ 核心特性

- **兼容 OpenAI API** - 直接替换 API 端点，无需修改代码
- **自动使用免费模型** - 无需手动切换，自动选择当前可用的免费模型
- **多 API 轮换** - 自动在多个免费 API 之间轮换，提高可用性
- **模块化架构** - 特殊 API（如 free5, free8）以独立服务运行，主服务保持轻量级
- **安全的密钥管理** - 从 `.env` 文件读取 API Key，不暴露在代码中
- **自动热重载** - 修改配置或代码后自动重新加载，无需重启服务
- **调试模式** - 保存所有请求/响应，便于问题排查
- **实时统计面板** - 网页面板直观显示今天的调用次数
- **智能重试机制** - 调用失败时自动重试，提高成功率
- **并发控制** - 限制同时处理的请求数，防止过载
- **故障隔离** - 独立服务崩溃不影响主服务和其他服务
- **权重系统** - 可配置 API 优先级，高权重 API 优先使用

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask requests watchdog python-dotenv
```

**注意：**
- Python 3.13+ 需要使用 watchdog 6.0.0 或更高版本
- 如果遇到线程错误，请升级：`pip install --upgrade watchdog`
- `python-dotenv` 用于加载 `.env` 文件

### 2. 配置 .env

```bash
# 你的 API Keys（从各平台获取）
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
FREE1_API_KEY=sk-or-v1-xxxxxxxxxxxxx
FREE3_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
# ... 其他 API Keys

# 缓存目录
CACHE_DIR=./cache

# HTTP 代理（如需要）
HTTP_PROXY=http://127.0.0.1:7897
```

### 3. 启动服务

```bash
# 方式一：启动所有服务（推荐）
035-start_all_services.bat

# 方式二：GUI 启动器
036-start_all_services_gui.bat

# 方式三：单独启动主服务
cd multi_free_api_proxy
python multi_free_api_proxy_v3_optimized.py

# 或使用批处理文件
start_proxy.bat

# 方式四：Go 版本（高性能）
050-start_api_proxy_go.bat
```

### 4. 配置你的工具

将 API 端点改为：

```
http://localhost:5000/v1
```

### 5. 运行测试（可选）

```bash
# 测试 Python 版本
020-test-on5001.bat

# 测试 Go 版本
040-test-api-proxy-go.bat
```

## 📚 文档

- [详细文档](./API_PROXY_README.md) - 完整的 API 文档和配置指南
- [多 API 文档](./multi_free_api_proxy/MULTI_FREE_API_README.md) - 多 API 代理服务文档
- [free_api_test README](./free_api_test/README.md) - 所有免费 API 详细说明
- [Go 版本文档](./api-proxy-go/README.md) - Go 版本 API 代理服务文档

## 🔧 文件说明

| 文件/目录 | 说明 |
|-----------|------|
| `multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py` | 主代理服务程序（推荐使用） |
| `free_api_test/` | 免费 API 配置目录 |
| `api-proxy-go/` | Go 版本 API 代理服务（高性能） |
| `start_proxy.bat` | Windows 启动脚本 |
| `035-start_all_services.bat` | 一键启动所有服务 |
| `036-start_all_services_gui.bat` | GUI 启动器 |
| `050-start_api_proxy_go.bat` | Go 版本启动脚本 |
| `.env` | 配置文件（需要自己配置 API Keys） |
| `DEBUG_MODE.txt` | 调试模式开关 |

## 🌐 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | 聊天完成（兼容 OpenAI） |
| `/v1/models` | GET | 列出可用模型 |
| `/health` | GET | 健康检查 |
| `/debug` | GET | 调试面板（需启用调试模式） |
| `/debug/stats` | GET | 调用统计 JSON（需启用调试模式） |

## 📚 免费 API 列表

感谢以下平台提供免费 API 服务（排名不分先后）：

| API | 服务商 | 模型 | 状态 | 代理 |
|-----|--------|------|------|------|
| free1 | OpenRouter | openrouter/free | ✅ | 需要 |
| free2 | ChatAnywhere | gpt-3.5-turbo | ✅ | 否 |
| free3 | Free.v36.cm | gpt-4o-mini | ✅ | 否 |
| free4 | Mistral AI | mistral-small | ✅ | 否 |
| free5 | iFlow SDK | various | ❌ 已关停 | - |
| free6 | CSDN | DeepSeek-V3 | ✅ | 否 |
| free7 | NVIDIA | nvidia/llama | ✅ | 否 |
| free8 | Friendli.ai | llama-3.3-70B | ✅ | 独立服务 |
| free9 | 火山引擎 | ark-code-latest | ⚠️ | 否 |
| free10 | 阿里云 Qwen | qwen-turbo | ⚠️ | 否 |
| free11 | OpenAI兼容 | gpt-4o-mini | ⚠️ | 需代理 |
| free12 | 硅基流动 | Qwen2.5-7B-Instruct | ⚠️ | 否 |
| free13 | Volcengine | ark-code-latest | ✅ | 否 |
| free14 | CogView | cgc-apikey | ✅ | 否 |
| free15 | Groq | llama-3.3-70b | ✅ | **需要** |
| free16 | Sambanova | DeepSeek-V3.1 | ✅ | 否 |
| free17 | Cerebras | llama3.1-8b | ✅ | **需要** |
| free18 | Google Gemini | gemini-3-flash | ✅ | **需要** |
| free19-20 | 新增 API | various | ✅ | 否 |

**说明：**
- ✅ 表示已测试可用
- ❌ 已关停 表示服务已停止
- ⚠️ 表示可能存在限制，请以官网为准
- "独立服务" 表示需要单独启动服务（free8）
- "需要" 表示需要通过 HTTP 代理访问

---

### 🙏 特别致谢

**free5 - iFlow SDK**：2025年3月正式关停，令人遗憾。这是一个非常优秀的服务，为开发者提供了极佳的体验。感谢 iFlow 团队曾经的付出！

### 💡 文明使用倡议

免费 API 是平台给予开发者的一份珍贵礼物，请大家：
- **感恩使用**：体验后如项目有收益，建议转付费支持平台可持续发展
- **节约资源**：避免无意义的重复请求，合理设置参数
- **遵守规则**：遵守各平台的使用条款，不滥用、不恶意请求
- **时间就是生命**：免费 API 稳定性有限，如需稳定服务，请选择付费方案

## 💡 使用示例

### Python

```python
import requests

response = requests.post(
    "http://localhost:5000/v1/chat/completions",
    json={
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
print(response.json())
```

### cURL

```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## ⚙️ 配置选项

### .env 文件

```bash
# 必需：API Keys
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
FREE1_API_KEY=sk-or-v1-xxxxxxxxxxxxx
# ... 其他 API Keys

# 可选：调试模式下的缓存目录
CACHE_DIR=./cache

# 可选：HTTP 代理（如需要）
HTTP_PROXY=http://127.0.0.1:7897

# 可选：最大并发请求数（默认为5）
MAX_CONCURRENT_REQUESTS=5
```

## 🔄 自动重载

修改以下文件后，下一个请求会自动重新加载配置，无需手动重启：

- `multi_free_api_proxy/.env` - 环境变量配置
- `multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py` - 代码文件
- `multi_free_api_proxy/config.py` - 配置文件

## 📊 调用统计

启用调试模式后，每天会自动生成统计文件：

**文件位置:** `{CACHE_DIR}/CALLS_YYYYMMDD.json`

**文件内容:**

```json
{
  "date": "20260216",
  "total": 10,
  "success": 7,
  "failed": 2,
  "timeout": 1,
  "retry": 3,
  "last_updated": "2026-02-16T20:30:45.123456"
}
```

## 🛡️ 守护进程

支持守护进程模式，异常退出时自动重启：

```bash
python daemon.py start    # 启动守护进程
python daemon.py stop     # 停止守护进程
python daemon.py status   # 查看状态
python daemon.py restart  # 重启守护进程
```

## ⚠️ 注意事项

- 确保 API Keys 有效
- 免费模型可能随时变化，建议定期检查各平台官网
- 调试模式会产生大量文件，建议仅在需要时启用
- 代理服务默认监听 `localhost:5000`，如需外网访问需修改代码
- 某些 API（如 free15, free17, free18）需要通过代理访问

## 🆘 故障排除

### 连接被拒绝

- 确保服务正在运行
- 检查端口 5000 是否被占用

### API Key 错误

- 检查 `.env` 文件中的 API Keys
- 确保 API Keys 有效且未过期

### 模型不可用

- 免费模型会定期变化
- 检查各平台官网了解当前可用的免费模型

### Python 3.13 线程错误

**解决方案：**
```bash
pip install --upgrade watchdog
```

需要升级到 watchdog 6.0.0 或更高版本。

## 📝 许可证

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 🔌 添加新的免费 API

1. 在 `free_api_test/` 目录下创建新目录 `free{N}`
2. 创建 `config.py` 文件，参考现有配置
3. 创建 `README.md` 文档
4. 创建 `test_api.py` 测试脚本
5. 在 `.env` 文件中添加 API Key
6. 重启服务

详见：[free_api_test/README.md](./free_api_test/README.md)

## 🆘 故障排除

### 连接被拒绝

- 确保服务正在运行
- 检查端口 5000（Python）或 5060（Go）是否被占用

### API Key 错误

- 检查 `multi_free_api_proxy/.env` 文件中的 API Keys
- 确保 API Keys 有效且未过期

### 模型不可用

- 免费模型会定期变化
- 检查各平台官网了解当前可用的免费模型
- 访问调试面板查看各 API 状态：http://localhost:5000/debug

### Python 3.13 线程错误

**解决方案：**
```bash
pip install --upgrade watchdog
```

需要升级到 watchdog 6.0.0 或更高版本。

### Go 版本服务问题

**解决方案：**
```bash
# 检查服务是否运行
curl http://localhost:5060/health

# 访问调试页面
# http://localhost:5060/debug

# 重启 Go 版本
050-start_api_proxy_go.bat

# 测试 Go 版本
040-test-api-proxy-go.bat
```

详见：[api-proxy-go/README.md](./api-proxy-go/README.md)

---

## 🔄 Python版 vs Go版 差异说明

### 端口和调试页面

| 版本 | 端口 | 调试页面 | 健康检查 |
|------|------|----------|----------|
| **Python (GUI)** | `5000` | http://localhost:5000/debug | 无定期检查 |
| **Go 版本** | `5060` | http://localhost:5060/debug | 每12小时定期检查 |

### 可用上游判断逻辑差异

| 特性 | Python 版本 | Go 版本 |
|------|-------------|---------|
| **判断依据** | 启动时 API 测试 + 失败黑名单(60秒) | 健康检查 (12小时周期) + Enabled配置 |
| **失败后行为** | 60秒后解除黑名单重新测试 | 连续失败3次永久标记不可用 |
| **配置来源** | `free_api_test/free{N}/config.py` | `upstreams/{name}/config.yaml` (通过 migrate_config.py 迁移) |

### 为什么两边显示的可用上游不同？

1. **检测机制不同**：
   - Python: 某些上游可能因失败被加入60秒黑名单，过期后重新测试
   - Go: 健康检查失败后连续失败达到阈值才标记不可用

2. **配置可能不同**：
   - Python 版本可能加载了所有 `free_api_test` 中的 API
   - Go 版本只加载了迁移的 `upstreams` 目录中的配置

3. **API Key 状态不同**：
   - 某些 API Key 可能在某个版本中配置正确，在另一个版本中缺失

### 故障排查步骤

1. **访问两边的调试页面对比**：
   - Python: http://localhost:5000/debug
   - Go: http://localhost:5060/debug

2. **检查 Go 版本控制台日志**：
   - 查看健康检查失败的具体错误信息
   - 日志格式：`[健康检查] xxx 已失效: xxx`

3. **检查 API Key 配置**：
   - Python: 检查 `.env` 文件
   - Go: 检查 `upstreams/{name}/config.yaml` 中的 `api_key` 字段

4. **查看具体上游状态**：
   - 访问 `/debug/apis` 接口查看每个上游的详细状态
   - 关注 `consecutive_failures` 和 `last_test_result` 字段
