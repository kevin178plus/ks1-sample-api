# free_chatgpt_api

## 免费版	
完全免费使用以下勾选模型：
 gpt-4o-mini
 gpt-3.5-turbo-0125
 gpt-3.5-turbo-1106
 gpt-3.5-turbo
 gpt-3.5-turbo-16k

## 一天总共可用200次

## key
您的免费API Key为: sk-t76****dD8

## API地址
	本项目当前API地址已更新为 https://free.v36.cm 请知晓！



## demo chat

```
import os
import openai

# optional; defaults to `os.environ['OPENAI_API_KEY']`
openai.api_key = "您的APIKEY"

# all client options can be configured just like the `OpenAI` instantiation counterpart
openai.base_url = "https://free.v36.cm/v1/"
openai.default_headers = {"x-foo": "true"}

completion = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "user",
            "content": "Hello world!",
        },
    ],
)
print(completion.choices[0].message.content)

# 正常会输出结果：Hello there! How can I assist you today ?
```