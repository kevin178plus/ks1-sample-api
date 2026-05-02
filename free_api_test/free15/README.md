# Groq API

## 概述
Groq提供超快的LLM推理服务，支持Llama系列模型。

## 支持的模型
- llama-3.3-70b-versatile (推荐)
- llama3-groq-70b-8192-tool-use-preview
- llama3-groq-8b-8192-tool-use-preview
- gemma-7b-it
- gemma2-9b-it
- llama-3.1-8b-instant
- llama-3.2-1b-preview
- llama-3.2-3b-preview
- llama-3.2-11b-vision-preview
- llama-3.2-90b-vision-preview

完整模型列表请访问: https://console.groq.com/docs/models

## API Key
从 https://console.groq.com/keys 获取API Key

## API地址
https://api.groq.com/openai/v1

## 使用示例

```python
import requests
import json

url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama-3.3-70b-versatile",
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
1. Groq提供免费额度，具体请查看官网
2. 免费模型有速率限制
3. **需要通过代理访问** (127.0.0.1:7897)
4. 建议在生产环境中监控使用情况
