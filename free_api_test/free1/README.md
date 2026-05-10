# OpenRouter API (free1)

## 概述
OpenRouter是一个统一的API网关,可以访问多个AI模型提供商。

## 配置
- **环境变量：** `FREE1_API_KEY`
- **默认模型：** `openrouter/free`
- **是否使用代理：** 是（需要配置 `HTTP_PROXY`）
- **默认权重：** 120

## API地址
https://openrouter.ai/api/v1/

## 使用示例

### 使用 new-demo.py（推荐）

```bash
cd free_api_test/free1
python new-demo.py
```

脚本会自动：
1. 从项目根目录加载 `.env` 文件
2. 读取 `FREE1_API_KEY`
3. 使用代理（如果配置了 `HTTP_PROXY`）
4. 调用 OpenRouter API

### 使用 test_api.py（完整测试）

```bash
cd free_api_test/free1
python test_api.py
```

会执行：
1. 模型列表 API 测试
2. 聊天完成 API 测试
3. 结果保存到 `test_result.txt`

### 直接调用

```python
import requests
import os
from dotenv import load_dotenv

# 从项目根目录加载 .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('FREE1_API_KEY')}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "Free API Demo"
}

payload = {
    "model": "openrouter/free",
    "messages": [{"role": "user", "content": "Hello!"}]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

## 支持的模型
OpenRouter支持大量模型,包括:
- `openrouter/free` (免费模型)
- `openai/gpt-3.5-turbo`
- `openai/gpt-4`
- `anthropic/claude-3-opus`
- `google/gemini-pro`
- 以及更多...

完整模型列表请访问: https://openrouter.ai/models

## 注意事项
1. API Key 配置在项目根目录的 `.env` 文件中
2. 免费模型有使用限制,请查看OpenRouter官网了解详情
3. free1 需要使用代理访问 OpenRouter，确保 `.env` 中配置了 `HTTP_PROXY`
4. 建议在生产环境中使用付费模型以获得更好的性能和稳定性
