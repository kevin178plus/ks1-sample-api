# OpenRouter 本地 API 代理

一个轻量级的本地 API 代理服务，让你无需配置复杂的 One API，直接在本机启动一个兼容 OpenAI API 格式的代理，自动使用 OpenRouter 的免费模型。

## 🎯 为什么需要这个项目？

- **One API 配置复杂**: One API 功能强大但配置繁琐，仅为了使用免费模型显得过度
- **免费模型经常变化**: OpenRouter 的免费模型列表经常更新，手动维护很麻烦
- **多工具集成困难**: 不同的工具需要配置不同的 API 端点，维护成本高
- **调用次数难以追踪**: 无法直观看到今天用了多少次免费 API

## ✨ 核心特性

- **兼容 OpenAI API** - 直接替换 API 端点，无需修改代码
- **自动使用免费模型** - 无需手动切换，自动选择当前可用的免费模型
- **安全的密钥管理** - 从 `.env` 文件读取 API Key，不暴露在代码中
- **自动热重载** - 修改配置或代码后自动重新加载，无需重启服务
- **调试模式** - 保存所有请求/响应，便于问题排查
- **实时统计面板** - 网页面板直观显示今天的调用次数
- **🆕 智能重试机制** - 调用失败时自动重试，提高成功率
- **🆕 并发控制** - 限制同时处理的请求数，防止过载

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask requests watchdog
```

### 2. 配置 .env

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
CACHE_DIR=./cache
```

### 3. 启动服务

```bash
python local_api_proxy.py
```

或在 Windows 上：

```bash
start_proxy.bat
```

### 4. 配置你的工具

将 API 端点改为：

```
http://localhost:5000/v1
```

## 📚 文档

- [详细文档](./API_PROXY_README.md) - 完整的 API 文档和配置指南

## 🔧 文件说明

| 文件 | 说明 |
|------|------|
| `local_api_proxy.py` | 代理服务主程序 |
| `start_proxy.bat` | Windows 启动脚本 |
| `test_local_proxy.py` | 测试脚本 |
| `.env` | 配置文件（需要自己创建） |
| `DEBUG_MODE.txt` | 调试模式开关（创建此文件启用） |

## 🌐 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | 聊天完成（兼容 OpenAI） |
| `/v1/models` | GET | 列出可用模型 |
| `/health` | GET | 健康检查 |
| `/debug` | GET | 调试面板（需启用调试模式） |
| `/debug/stats` | GET | 调用统计 JSON（需启用调试模式） |
| `/debug/concurrency` | GET | 并发状态和调用历史（需启用调试模式） |

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

## 🐛 调试模式

创建 `DEBUG_MODE.txt` 文件启用调试模式：

```bash
# Windows
type nul > DEBUG_MODE.txt

# Linux/Mac
touch DEBUG_MODE.txt
```

启用后：
- 所有请求/响应会保存到 `CACHE_DIR` 目录
- 访问 `http://localhost:5000/debug` 查看实时统计面板
- 访问 `http://localhost:5000/debug/stats` 获取 JSON 统计数据

## ⚙️ 配置选项

### .env 文件

```bash
# 必需：OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# 可选：调试模式下的缓存目录
CACHE_DIR=./cache

# 可选：HTTP 代理（如需要）
HTTP_PROXY=http://proxy:port

# 可选：最大并发请求数（默认为5）
MAX_CONCURRENT_REQUESTS=5
```

## 🔄 自动重载

修改以下文件后，下一个请求会自动重新加载配置，无需手动重启：

- `.env` - 环境变量配置
- `local_api_proxy.py` - 代码文件

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

**字段说明:**
| 字段 | 说明 |
|------|------|
| `total` | 总调用次数 |
| `success` | 成功次数 |
| `failed` | 失败次数 |
| `timeout` | 超时次数 |
| `retry` | 自动重试次数 |

## 🛡️ 守护进程

支持守护进程模式，异常退出时自动重启：

**启动守护进程:**
```bash
# 方式1: 直接启动
python daemon.py start

# 方式2: 使用批处理文件
010-start_proxy_daemon-start.bat
```

**管理命令:**
```bash
python daemon.py start    # 启动守护进程
python daemon.py stop     # 停止守护进程
python daemon.py status   # 查看状态
python daemon.py restart  # 重启守护进程
```

**特性:**
- 单例保护：防止重复启动
- 自动重启：异常退出时自动重启（最多10次/分钟）
- 日志记录：写入 `daemon.log`
- **🆕 集中管理**：`daemon.log` 和 `daemon.pid` 默认放在 `CACHE_DIR` 目录
- **🆕 灵活配置**：支持通过 `CACHE_DIR` 环境变量自定义位置

**文件位置:**
- 如果设置了 `CACHE_DIR`：`{CACHE_DIR}/daemon.log` 和 `{CACHE_DIR}/daemon.pid`
- 如果未设置 `CACHE_DIR`：项目根目录的 `daemon.log` 和 `daemon.pid`

详见：[DAEMON_IMPROVEMENT.md](./DAEMON_IMPROVEMENT.md)

## ⚠️ 注意事项

- 确保 OpenRouter API Key 有效
- 免费模型可能随时变化，建议定期检查 OpenRouter 官网
- 调试模式会产生大量文件，建议仅在需要时启用
- 代理服务默认监听 `localhost:5000`，如需外网访问需修改代码

## 🆘 故障排除

### 连接被拒绝

- 确保服务正在运行
- 检查端口 5000 是否被占用

### API Key 错误

- 检查 `.env` 文件中的 `OPENROUTER_API_KEY`
- 确保 API Key 有效且未过期

### 模型不可用

- OpenRouter 的免费模型会定期变化
- 检查 [OpenRouter 官网](https://openrouter.ai) 了解当前可用的免费模型

## 📝 许可证

MIT

## 🆕 新增功能详解

### 智能重试机制

当 API 调用失败时，系统会根据以下条件自动重试一次：
- 今天前3次调用中有失败，或
- 最近3次调用中有成功

详见 [FEATURES_UPDATE.md](./FEATURES_UPDATE.md)

### 并发控制

限制同时处理的请求数量，防止服务过载。通过 `MAX_CONCURRENT_REQUESTS` 配置（默认5）。

详见 [FEATURES_UPDATE.md](./FEATURES_UPDATE.md)

### 🆕 reasoning 字段自动处理

某些模型（如 nvidia/nemotron 系列）会在 `reasoning` 字段中返回思考过程，而 `content` 字段可能为空。代理会自动检测这种情况，当 `content` 为空但存在 `reasoning` 时，自动将 `reasoning` 的内容复制到 `content` 字段中，确保客户端能正常获取回复内容。

**相关代码位置：** [local_api_proxy.py:337-341](file:///d:/ks_ws/git-root/ks1-simple-api/local_api_proxy.py#L337-L341)

### 🆕 调试界面参数可调

在调试面板的测试聊天页面中，新增了 `max_tokens` 参数输入框，可以实时调整AI回复的最大长度。

**功能特性：**
- 默认值：1000
- 可调范围：100-4000
- 步长：100
- 实时生效，无需重启

**使用方法：**
1. 访问 `http://localhost:5000/debug`
2. 切换到"测试聊天"标签
3. 在"Max Tokens"输入框中调整参数值
4. 发送消息测试效果

**相关代码位置：**
- 前端界面：[local_api_proxy.py:1030-1040](file:///d:/ks_ws/git-root/ks1-simple-api/local_api_proxy.py#L1030-L1040)
- 参数使用：[local_api_proxy.py:1160](file:///d:/ks_ws/git-root/ks1-simple-api/local_api_proxy.py#L1160)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
