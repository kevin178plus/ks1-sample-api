# 🚀 API 代理服务 - 多场景部署方案

一个轻量级的 API 代理，兼容 OpenAI API 格式，专门用于 OpenRouter 的免费模型。支持多种部署场景，从本地开发到生产环境，总有一款适合你。

> 🎯 **快速选择场景**：查看 `scenarios/README.md` 根据需求选择最适合的部署方案

## 核心功能

- ✅ 兼容 OpenAI API 格式（可直接替换 API 端点）
- ✅ 自动使用 OpenRouter 免费模型（无需手动切换）
- ✅ 从 `.env` 文件读取 API Key（安全且方便）
- ✅ 自动监控文件变化（修改配置自动重新加载，无需重启）
- ✅ 调试模式（保存所有请求/响应，实时查看调用次数）
- ✅ 网页调试面板（统计信息 + 测试聊天 + 性能监控）

## 🎯 部署场景选择

### 📋 场景概览
| 场景 | 适用环境 | 安全级别 | 复杂度 | 入口 |
|------|----------|----------|--------|------|
| 🖥️ **win2012-server** | Windows Server 2012 R2 (2GB内存) | 中等 | 简单 | [进入 →](scenarios/win2012-server/) |
| 🚀 **simple-deployment** | 快速部署、内网访问 | 基础 | 最简 | [进入 →](scenarios/simple-deployment/) |
| 🛠️ **development** | 本地开发、测试调试 | 基础 | 中等 | [进入 →](scenarios/development/) |
| 🏭 **production** | 生产环境、企业级 | 最高 | 复杂 | [进入 →](scenarios/production/) |

### 🌟 推荐选择
- **新手/快速部署** → 🚀 simple-deployment
- **老旧服务器** → 🖥️ win2012-server  
- **本地开发** → 🛠️ development
- **生产环境** → 🏭 production

> 📖 **详细指南**：查看 [`scenarios/README.md`](scenarios/README.md) 了解各场景详细对比

---

## 🚀 优化版本说明

我们为不同场景提供了优化版本，推荐使用：

### 🛠️ 开发环境优化版
- **文件**: `scenarios/development/*_optimized.*`
- **改进**: 30秒超时、缓存限制、中文支持、详细错误处理
- **适用**: 本地开发、测试调试
- **路径**: 自动切换到项目根目录运行，统一配置管理

### 🖥️ 老旧服务器安全版  
- **文件**: `scenarios/win2012-server/minimal_setup.bat`
- **改进**: 零系统影响、只配置必需项
- **适用**: Windows Server 2012 R2 + 新手

### 🔄 回退机制
所有修改都提供完整的回退脚本，确保系统安全。

---

## 📁 原始版本（开发调试）

以下为原始的本地开发版本，仍可继续使用：

### 🎯 **重要路径说明**
**注意：** 双击 `scenarios/development/` 目录下的批处理文件时：
- ✅ **实际运行：** 项目根目录的 `local_api_proxy.py` 
- ✅ **配置读取：** 项目根目录的 `.env` 文件
- 🔄 **自动切换：** 批处理文件会自动切换到项目根目录执行

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

**方式一：使用场景脚本（推荐）**
```bash
# 进入开发场景目录
cd scenarios/development

# 双击批处理文件，会自动切换到根目录运行
start_proxy.bat
# 或
start_proxy_optimized.bat
```

**方式二：直接运行**
```bash
# 在项目根目录执行
python local_api_proxy.py
```

服务将在 `http://localhost:5000` 启动

### 4. 测试服务

```bash
# 在项目根目录执行测试
python test_local_proxy.py
```

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

打开功能丰富的调试面板网页，包含：

#### 📊 统计信息页面
- 实时显示今天的调用次数
- 每日调用统计和最后更新时间
- 每 30 秒自动刷新数据

#### 💬 测试聊天页面
- **直接对话测试**：在网页中直接输入问题与AI对话
- **响应时间显示**：精确显示每个请求的延迟（毫秒）
- **实时状态指示**：显示发送状态和加载进度
- **错误友好提示**：详细显示错误信息和响应状态
- **便捷操作**：支持 Enter 键快速发送

**使用方法：**
1. 启动代理服务
2. 访问 `http://localhost:5000/debug`
3. 点击"测试聊天"标签开始对话测试
4. 查看AI回复和详细的响应时间数据

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
