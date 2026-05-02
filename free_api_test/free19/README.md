# Cohere API

## 概述
Cohere提供企业级LLM服务，支持command系列模型。

## 支持的模型
- command-a-03-2025 (推荐)
- command-r7b-12-2025
- command-r-08-2024
- c4ai-uda-2

完整模型列表请访问: https://dashboard.cohere.com/api-keys

## API Key
从 https://dashboard.cohere.com/api-keys 获取API Key

## API地址
https://api.cohere.com/v2

## 使用示例

```python
import requests
import json

url = "https://api.cohere.com/v2/chat"

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload = {
    "model": "command-a-03-2025",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.3
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

## 注意事项
1. Cohere提供免费额度，具体请查看官网
2. 免费模型有速率限制
3. **需要通过代理访问** (127.0.0.1:7897)
4. 响应格式特殊：`message.content[0].text`