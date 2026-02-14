# 本地 API 代理服务

一个轻量级的本地 API 代理，兼容 OpenAI API 格式，专门用于 OpenRouter 的免费模型。无需配置复杂的 One API，直接在本机启动一个代理服务，让其他工具都指向它。

## 核心功能

- ✅ 兼容 OpenAI API 格式（可直接替换 API 端点）
- ✅ 自动使用 OpenRouter 免费模型（无需手动切换）
- ✅ 从 `.env` 文件读取 API Key（安全且方便）
- ✅ 自动监控文件变化（修改配置自动重新加载，无需重启）
- ✅ 调试模式（保存所有请求/响应，实时查看调用次数）
- ✅ 网页调试面板（直观显示今天的调用统计）

## 快速开始

### 1. 安装依赖

```bash
pip install flask requests watchdog
```

### 2. 配置 .env 文件

在项目根目录创建或编辑 `.env` 文件：

```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
CACHE_DIR=./cache
```

- `OPENROUTER_API_KEY`: 你的 OpenRouter API Key（必需）
- `CACHE_DIR`: 缓存目录路径（可选，调试模式下使用）

### 3. 启动服务

**Windows:**
```bash
start_proxy.bat
```

**或直接运行:**
```bash
python local_api_proxy.py
```

服务将在 `http://localhost:5000` 启动

### 4. 配置其他工具

将其他工具的 API 配置改为：

```
API Base URL: http://localhost:5000/v1
API Key: 任意值（代理会使用 .env 中的 key）
Model: openrouter/free
```

**Python 示例:**
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

**cURL 示例:**
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## API 端点

### POST /v1/chat/completions

标准的 OpenAI 聊天完成端点

**请求示例:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**响应示例:**
```json
{
  "id": "...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "openrouter/free",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### GET /v1/models

列出可用模型

### GET /health

健康检查

### GET /debug/stats (调试模式)

获取今天的调用统计（JSON 格式）

**响应示例:**
```json
{
  "date": "20240214",
  "count": 42,
  "last_updated": "2024-02-14T10:30:45.123456"
}
```

### GET /debug (调试模式)

打开调试面板网页，实时显示今天的调用次数，每 5 秒自动刷新一次

## 调试模式详解

### 启用调试模式

1. 在代理服务同目录创建 `DEBUG_MODE.txt` 文件
2. 在 `.env` 中添加 `CACHE_DIR` 配置（可选，不配置则不保存）

### 缓存文件格式

每个请求/响应都会生成一个 JSON 文件：

```json
{
  "timestamp": "2024-02-14T10:30:45.123456",
  "type": "REQUEST",
  "message_id": "a1b2c3d4",
  "data": {
    "messages": [...],
    "temperature": 0.7,
    ...
  }
}
```

### 文件名规则

- 格式: `YYYYMMDD_HHMMSS_mmm_TYPE_消息ID.json`
- 例如: `20240214_103045_123_REQUEST_a1b2c3d4.json`
- TYPE 可以是: REQUEST, RESPONSE, ERROR

### 每日调用统计

调试模式下会自动生成每日统计文件：

**文件名:** `CALLS_YYYYMMDD.json`

**文件内容:**

```json
{
  "date": "20240214",
  "count": 42,
  "last_updated": "2024-02-14T10:30:45.123456"
}
```

**查看方式:**

- 直接访问 `http://localhost:5000/debug` 打开网页面板
- 或访问 `http://localhost:5000/debug/stats` 获取 JSON 数据

## 配置示例

### Python requests

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
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 注意事项

- 确保 `.env` 文件中有 `OPENROUTER_API_KEY`
- 代理会自动使用 `openrouter/free` 模型
- 所有请求都会转发到 OpenRouter
- 代理不会缓存任何数据（除非启用调试模式）
- 修改 `.env` 或 `local_api_proxy.py` 后，下一个请求会自动重新加载配置，无需手动重启
- 调试模式会产生大量文件，建议仅在需要时启用

## 故障排除

### 连接被拒绝

- 确保代理服务正在运行
- 检查端口 5000 是否被占用

### API Key 错误

- 检查 `.env` 文件中的 `OPENROUTER_API_KEY`
- 确保 API Key 有效

### 模型不可用

- OpenRouter 的免费模型会定期变化
- 检查 OpenRouter 官网了解当前可用的免费模型
