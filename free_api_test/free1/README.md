# OpenRouter API

## 概述
OpenRouter是一个统一的API网关,可以访问多个AI模型提供商。

## 支持的模型
OpenRouter支持大量模型,包括:
- openrouter/free (免费模型)
- openai/gpt-3.5-turbo
- openai/gpt-4
- anthropic/claude-3-opus
- google/gemini-pro
- 以及更多...

完整模型列表请访问: https://openrouter.ai/models

## API Key
您需要从 https://openrouter.ai/keys 获取API Key

## API地址
https://openrouter.ai/api/v1/

## 使用示例

```python
import requests
import json

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "MyApp"
}

payload = {
    "model": "openrouter/free",
    "messages": [
        {
            "role": "user",
            "content": "Hello!"
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

## 注意事项
1. 请将test_api.py中的`your_openrouter_api_key_here`替换为您的实际API Key
2. 免费模型有使用限制,请查看OpenRouter官网了解详情
3. 建议在生产环境中使用付费模型以获得更好的性能和稳定性
