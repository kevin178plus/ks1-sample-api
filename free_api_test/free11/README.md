# Free API Test - 白山智算 API

本项目用于测试白山智算 API 的调用。

## 目录结构

```
free11/
├── README.md           # 本文件
├── config.py          # API 配置文件
├── test_api.py        # API 测试脚本
├── ask.txt            # 测试问题文件
├── local_api_proxy.py # 本地 API 代理服务（OpenAI 兼容）
├── .env               # 环境变量配置（API Key）
└── 白山智算API.txt     # API 文档
```

## API 信息

### API Key 获取
访问 https://ai.baishan.com/key/index 获取 API Key

### API 地址
https://api.edgefn.net/v1/chat/completions

### 支持的模型

1. **DeepSeek-R1-0528-Qwen3-8B**
   - 混合模型，结合了 DeepSeek 和 Qwen 的优势
   - 适合通用对话和复杂推理

2. **KAT-Coder-Exp-72B-1010**
   - 大型代码模型
   - 适合编程、代码生成、代码理解等任务

3. **MiniMax-M2.5**
   - 通用对话模型
   - 适合日常对话、内容生成

## 配置说明

### 环境变量 (.env)

在项目根目录的 `.env` 文件中配置以下变量：

```env
FREE11_API_KEY=your_api_key_here
```

或者在 `config.py` 中直接设置：

```python
API_KEY = "your_api_key_here"
```

### config.py

```python
API_KEY = os.getenv("FREE11_API_KEY")
BASE_URL = "https://api.edgefn.net"
MODEL = "DeepSeek-R1-0528-Qwen3-8B"
```

## 使用示例

### 1. 基础调用

```python
import requests

url = "https://api.edgefn.net/v1/chat/completions"
headers = {
    "Authorization": "{YOUR_API_KEY}",  # 注意：不需要 Bearer 前缀
    "Content-Type": "application/json"
}
data = {
    "model": "DeepSeek-R1-0528-Qwen3-8B",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

**注意：** 白山智算 API 的 Authorization header 直接使用 API key，不需要 `Bearer` 前缀。

### 2. 使用 test_api.py

```bash
python test_api.py
```

这个脚本会：
- 从 `ask.txt` 读取问题
- 调用白山智算 API
- 打印返回结果

### 3. 测试不同模型

修改 `config.py` 中的 `MODEL` 参数：

```python
# 使用代码模型
MODEL = "KAT-Coder-Exp-72B-1010"

# 使用 MiniMax 模型
MODEL = "MiniMax-M2.5"
```

### 4. 使用本地 API 代理服务

本地 API 代理服务提供了一个 OpenAI 兼容的接口，可以直接在本地运行。

**启动服务：**

```bash
python local_api_proxy.py
```

**服务端点：**

- API 端点：`http://localhost:5000/v1/chat/completions`
- 模型列表：`http://localhost:5000/v1/models`
- 健康检查：`http://localhost:5000/health`
- 调试面板：`http://localhost:5000/debug`

**使用代理：**

```python
import requests

# 通过代理调用白山智算 API
response = requests.post('http://localhost:5000/v1/chat/completions', json={
    'model': 'DeepSeek-R1-0528-Qwen3-8B',
    'messages': [{'role': 'user', 'content': '你好'}]
})
print(response.json())
```

**代理功能：**

- 自动重试机制（最多 3 次）
- 并发请求控制
- 请求/响应缓存（可选）
- 调试模式支持
- 文件监控，自动重新加载配置

**启用调试模式：**

在 free11 目录下创建 `DEBUG_MODE.txt` 文件即可启用调试模式，所有请求和响应将被保存到缓存目录。

## API 数据结构

### 请求格式

```json
{
  "model": "DeepSeek-R1-0528-Qwen3-8B",
  "messages": [
    {
      "role": "user",
      "content": "你的问题"
    }
  ]
}
```

### 响应格式

```json
{
  "id": "chatcmpl-xxxxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "DeepSeek-R1-0528-Qwen3-8B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "AI 的回答内容"
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

## 使用建议

### 模型选择

- **通用对话**：使用 `DeepSeek-R1-0528-Qwen3-8B` 或 `MiniMax-M2.5`
- **代码相关**：使用 `KAT-Coder-Exp-72B-1010`
- **复杂推理**：使用 `DeepSeek-R1-0528-Qwen3-8B`

### 模型性能

根据实际测试：

| 模型 | 响应速度 | 推荐超时 | 适用场景 |
|------|----------|----------|----------|
| DeepSeek-R1-0528-Qwen3-8B | 快 | 30秒 | 通用对话、推理 |
| KAT-Coder-Exp-72B-1010 | 慢 | 60-120秒 | 代码生成、编程 |
| MiniMax-M2.5 | 快 | 30秒 | 日常对话、内容生成 |

**注意：** KAT-Coder-Exp-72B-1010 是 72B 大模型，响应时间较长，建议增加超时时间。

### 参数调优

- `temperature`: 控制输出的随机性
  - 0.0-0.3: 更确定性的输出
  - 0.5-0.7: 平衡创造性和确定性（推荐）
  - 0.8-1.0: 更有创造性的输出

- `max_tokens`: 控制返回内容的长度
  - 简单问题：1000-2000
  - 复杂问题：2000-4000

### 代理服务配置

在 `.env` 文件中可以配置代理服务的额外参数：

```env
FREE11_API_KEY=your_api_key_here
TEST_MODE=false              # 测试模式
HTTP_PROXY=http://127.0.0.1:7890  # HTTP 代理（可选）
MAX_CONCURRENT_REQUESTS=5    # 最大并发请求数
CACHE_DIR=./cache            # 缓存目录（调试模式使用）
```

## 注意事项

1. API Key 需要保密，不要提交到版本控制系统
2. 注意 API 的调用频率限制
3. 不同模型的性能和能力差异较大，请根据实际需求选择
4. 建议在生产环境中添加错误处理和重试机制

## 更新日志

- 2026-03-08: 初始版本，支持 DeepSeek-R1-0528-Qwen3-8B、KAT-Coder-Exp-72B-1010、MiniMax-M2.5 模型
- 2026-03-08: 添加本地 API 代理服务（local_api_proxy.py），提供 OpenAI 兼容接口
- 2026-03-08: 测试验证所有模型，确认代理服务正常工作
- 2026-03-08: 修复 Authorization header 格式（不需要 Bearer 前缀）