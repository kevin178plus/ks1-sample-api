# Cerebras API

## 概述
Cerebras提供高性能的LLM推理服务，支持Llama系列模型。

## 支持的模型
- llama3.1-8b (推荐)
- llama3.1-70b
- llama3.1-8b-instruct
- llama3.1-70b-instruct

完整模型列表请访问: https://www.cerebras.ai/

## API Key
从 https://www.cerebras.ai/ 获取API Key

## API地址
https://api.cerebras.ai/v1

## 使用示例

### HTTP API
```python
import requests
import json

url = "https://api.cerebras.ai/v1/chat/completions"

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

payload = {
    "model": "llama3.1-8b",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "max_completion_tokens": 1024
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### SDK
```python
from cerebras.cloud.sdk import Cerebras

client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))
completion = client.chat.completions.create(
    messages=[{"role":"user","content":"Hello!"}],
    model="llama3.1-8b",
    max_completion_tokens=1024
)
print(completion.choices[0].message.content)
```

## 注意事项
1. Cerebras提供免费额度，具体请查看官网
2. 免费模型有速率限制
3. 建议在生产环境中监控使用情况
