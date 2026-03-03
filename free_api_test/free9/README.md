-- 13:56 2026/2/28 火山方舟大模型服务平台
> https://www.volcengine.com/docs/82379/2188959?lang=zh#8acf9b21

API Provider：OpenAI Compatible（Coding Plan 接口兼容 OpenAI 标准）
Base URL：https://ark.cn-beijing.volces.com/api/coding
Endpoint：/v3/chat/completions
API Key：获取API Key
Model：支持配置ark-code-latest、配置 Model Name 两种方式，具体见核心配置。


## 获取API Key
> https://console.volcengine.com/ark/region:ark+cn-beijing/apikey?apikey=%7B%7D
api-key-20260228135726
	88**58b


## 文档首页 > 火山方舟大模型服务平台 > Coding Plan > 接入 AI 编程工具 > OpenClaw (原 Clawdbot)

OpenClaw (原 Clawdbot)

### Base URL
	不同的工具配置的 Base URL 根据兼容的协议会有不同：
	兼容 Anthropic 接口协议工具：https://ark.cn-beijing.volces.com/api/coding
	兼容 OpenAI 接口协议工具：https://ark.cn-beijing.volces.com/api/coding/v3

	注意:请勿使用 https://ark.cn-beijing.volces.com/api/v3 ：该 Base URL 不会消耗您的 Coding Plan 额度，而是会产生额外费用。

### API Key
	获取 API Key	https://console.volcengine.com/ark/region:ark+cn-beijing/apikey


### Settings - Config - Authentication，在底部选择 Raw 方式查看并修改配置信息。
```
"models": {
    "providers": {
      "volcengine": {
        "baseUrl": "https://ark.cn-beijing.volces.com/api/coding/v3",
        "apiKey": "<ARK_API_KEY>",
        "api": "openai-completions",
        "models": [
          {
            "id": "ark-code-latest",
            "name": "ark-code-latest",
            "reasoning": false,
            "input": [
              "text"
            ],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
 }
```

## 本项目配置说明

在本项目的 `config.py` 中，为了适配代理服务的要求，配置如下：

```python
API_KEY = os.getenv("FREE9_API_KEY")
BASE_URL = "https://ark.cn-beijing.volces.com/api/coding"
ENDPOINT = "/v3/chat/completions"  # 火山方舟使用 /v3 而非 /v1
MODEL_NAME = "ark-code-latest"
```

**注意**：火山方舟的完整端点路径是 `https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions`，代理代码会自动拼接 `BASE_URL + ENDPOINT`。
