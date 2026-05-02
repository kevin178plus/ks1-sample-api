# Google Gemini API

## 概述
Google Gemini提供先进的多模态AI模型服务。

## 支持的模型
- gemini-3-flash-preview (推荐)
- gemini-2.0-flash-exp
- gemini-1.5-flash
- gemini-1.5-pro
- gemini-1.5-pro-8b

完整模型列表请访问: https://ai.google.dev/gemini-api/docs/models

## API Key
从 https://aistudio.google.com/app/apikey 获取API Key

## API地址
https://generativelanguage.googleapis.com/v1beta

## 使用示例

### SDK
```python
from google import genai

client = genai.Client(api_key="YOUR_API_KEY")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Hello!"
)

print(response.text)
```

### HTTP API
```python
import requests

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key=YOUR_API_KEY"

headers = {
    "Content-Type": "application/json"
}

payload = {
    "contents": [{
        "parts": [{"text": "Hello!"}]
    }]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

## 注意事项
1. Gemini提供免费额度，具体请查看官网
2. 免费模型有速率限制
3. **需要通过代理访问**
4. 建议在生产环境中监控使用情况
