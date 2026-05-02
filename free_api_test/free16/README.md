# Sambanova API

## 概述
Sambanova提供高性能的LLM推理服务，支持DeepSeek系列模型。

## 支持的模型
- DeepSeek-V3.1 (推荐)
- DeepSeek-R1
- Llama-3.1-70B
- Llama-3.1-405B
- Meta-Llama-3.3-70B

完整模型列表请访问: https://cloud.sambanova.ai/apis

## API Key
从 https://cloud.sambanova.ai/apis 获取API Key

## API地址
https://api.sambanova.ai/v1

## 使用示例

```python
import requests
import json

url = "https://api.sambanova.ai/v1/chat/completions"

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

payload = {
    "model": "DeepSeek-V3.1",
    "messages": [
        {"role": "user", "content": "Hello!"}
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

## 注意事项
1. Sambanova提供免费额度，具体请查看官网
2. 免费模型有速率限制
3. 建议在生产环境中监控使用情况
