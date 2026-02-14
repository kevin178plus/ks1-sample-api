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
  "date": "20240214",
  "count": 42,
  "last_updated": "2024-02-14T10:30:45.123456"
}
```

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

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
