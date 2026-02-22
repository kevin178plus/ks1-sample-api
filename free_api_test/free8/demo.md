## Python Demo

```
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("FRIENDLI_TOKEN"),
    base_url="https://api.friendli.ai/serverless/v1",
)

completion = client.chat.completions.create(
    model="zai-org/GLM-5",
    extra_body={},
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a funny joke."},
    ],
)

print(completion.choices[0].message.content)
```

## 200 返回格式类似

```
{
  "id": "chatcmpl-4b71d12c86d94e719c7e3984a7bb7941",
  "model": "meta-llama-3.1-8b-instruct",
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello there, how may I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 9,
    "completion_tokens": 11,
    "total_tokens": 20
  },
  "created": 1735722153
}
```