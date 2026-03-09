# Free API Test - OpenCode AI API

本项目用于测试 OpenCode AI API 的调用。

## 目录结构

```
free12/
├── README.md           # 本文件
├── config.py          # API 配置文件
├── test_api.py        # API 测试脚本
├── ask.txt            # 测试问题文件
└── test_result.txt    # 测试结果（运行后生成）
```

## API 信息

### API 地址
https://opencode.ai/zen/v1

### API 端点
- 聊天完成：`https://opencode.ai/zen/v1/chat/completions`

### 支持的模型
- **minimax-m2.5-free** - MiniMax M2.5 免费模型

## 配置说明

### 环境变量 (.env)

在项目根目录的 `.env` 文件中配置以下变量：

```env
FREE12_API_KEY=your_api_key_here
```

或者在 `config.py` 中直接设置：

```python
API_KEY = "your_api_key_here"
BASE_URL = "https://opencode.ai/zen/v1"
MODEL = "minimax-m2.5-free"
```

### config.py

```python
API_KEY = "your_api_key_here"
BASE_URL = "https://opencode.ai/zen/v1"
MODEL = "minimax-m2.5-free"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000
TIMEOUT = 60
```

## 使用示例

### 1. 基础调用

```python
import requests

url = "https://opencode.ai/zen/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "model": "minimax-m2.5-free",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "temperature": 0.7,
    "max_tokens": 2000
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### 2. 使用 test_api.py

```bash
cd free_api_test/free12
python test_api.py
```

这个脚本会：
- 从 `ask.txt` 读取问题
- 调用 OpenCode AI API
- 打印返回结果
- 保存结果到 `test_result.txt`

### 3. 修改测试问题

编辑 `ask.txt` 文件，添加你想要测试的问题。

## API 数据结构

### 请求格式

```json
{
  "model": "minimax-m2.5-free",
  "messages": [
    {
      "role": "user",
      "content": "你的问题"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### 响应格式

```json
{
  "id": "chatcmpl-xxxxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "minimax-m2.5-free",
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

## 参数说明

### temperature
控制输出的随机性：
- 0.0-0.3: 更确定性的输出
- 0.5-0.7: 平衡创造性和确定性（推荐）
- 0.8-1.0: 更有创造性的输出

### max_tokens
控制返回内容的长度：
- 简单问题：1000-2000
- 复杂问题：2000-4000

## 注意事项

1. API Key 需要保密，不要提交到版本控制系统
2. 注意 API 的调用频率限制
3. 建议在生产环境中添加错误处理和重试机制
4. 免费模型可能有使用限制

## 常见问题

### 请求超时
如果遇到超时错误，可以修改 `config.py` 中的 `TIMEOUT` 参数：
```python
TIMEOUT = 120  # 增加超时时间
```

### API 认证失败
确保 API Key 正确配置，检查是否有空格或特殊字符。

## 更新日志

- 2026-03-09: 初始版本，支持 minimax-m2.5-free 模型
