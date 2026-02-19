# Mistral AI API

## 简介
Mistral AI 是一家欧洲的 AI 公司，提供高性能的大语言模型服务。

## API 信息
- API 地址: https://api.mistral.ai/v1/
- 文档地址: https://docs.mistral.ai/

## 可用模型
- `mistral-small-latest` - 轻量级模型，快速响应
- `mistral-medium-latest` - 中等规模模型，平衡性能与质量
- `mistral-large-latest` - 大规模模型，最佳性能
- `open-mistral-nemo` - 开源模型

## API Key
需要设置环境变量 `MISTRAL_API_KEY`

## 使用示例

### cURL 示例
```bash
curl --location "https://api.mistral.ai/v1/chat/completions" \
     --header 'Content-Type: application/json' \
     --header 'Accept: application/json' \
     --header "Authorization: Bearer $MISTRAL_API_KEY" \
     --data '{
    "model": "mistral-medium-latest",
    "messages": [{"role": "user", "content": "Who is the most renowned French painter?"}]
  }'
```

### Python 示例
```python
import os
import openai

# 设置 API Key
openai.api_key = os.environ.get("MISTRAL_API_KEY")

# 设置 Mistral API 地址
openai.base_url = "https://api.mistral.ai/v1/"

# 调用 API
completion = openai.chat.completions.create(
    model="mistral-medium-latest",
    messages=[
        {
            "role": "user",
            "content": "Hello world!",
        },
    ],
)
print(completion.choices[0].message.content)
```

## 注意事项
1. Mistral API 兼容 OpenAI SDK 格式
2. 需要有效的 API Key 才能使用
3. API 有调用频率限制，请参考官方文档
