# CSDN API

## 概述

CSDN API 提供对 Deepseek-V3 模型的访问，这是一个高性能的大语言模型。

## 特性

- Deepseek-V3 模型访问
- OpenAI API 兼容格式
- 简单的配置方式
- 高性能响应

## 配置

### API 配置

在 `config.py` 文件中配置：

```python
# API配置
API_KEY = "your_api_key_here"
API_URL = "https://models.csdn.net/v1/chat/completions"
MODEL_NAME = "Deepseek-V3"
```

### 环境变量配置

也可以通过环境变量配置（推荐）：

```properties
# 在 .env 文件中
FREE6_API_KEY=your_api_key_here
```

## 使用示例

### 基础查询

```python
from config import API_KEY, API_URL, MODEL_NAME
import requests

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": MODEL_NAME,
    "messages": [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    "temperature": 0.7
}

response = requests.post(API_URL, headers=headers, json=data)
result = response.json()
print(result["choices"][0]["message"]["content"])
```

### 运行测试脚本

```bash
python test_api.py
```

## API 端点

### 聊天完成

**端点**: `POST https://models.csdn.net/v1/chat/completions`

**请求示例**:

```bash
curl -X POST https://models.csdn.net/v1/chat/completions   -H "Content-Type: application/json"   -H "Authorization: Bearer YOUR_API_KEY"   -d '{
    "model": "Deepseek-V3",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ],
    "temperature": 0.7
  }'
```

## 参数说明

### 请求参数

- `model` (string, required): 模型名称，固定为 "Deepseek-V3"
- `messages` (array, required): 消息数组，包含对话历史
- `temperature` (number, optional): 控制随机性，范围 0-1，默认 0.7
- `max_tokens` (number, optional): 最大生成 token 数
- `top_p` (number, optional): 核采样参数，范围 0-1

### 响应格式

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "Deepseek-V3",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "回复内容"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

## 集成到多 API 代理

CSDN API (free6) 已集成到 `multi_free_api_proxy_v3.py` 中，可以与其他 free API 一起使用。

配置方法：

1. 在 `.env` 文件中添加：
```properties
FREE6_API_KEY=your_csdn_api_key
```

2. 启动多 API 代理：
```bash
python multi_free_api_proxy/multi_free_api_proxy_v3.py
```

## 注意事项

1. API Key 需要从 CSDN 获取
2. 免费使用可能有调用频率限制
3. 建议在生产环境中监控使用情况
4. API 响应时间可能因请求复杂度而异

## 错误处理

常见错误及解决方案：

1. **401 Unauthorized**
   - 原因：API Key 无效或过期
   - 解决方案：检查 API Key 是否正确

2. **429 Too Many Requests**
   - 原因：超过调用频率限制
   - 解决方案：等待一段时间后重试

3. **500 Internal Server Error**
   - 原因：服务器内部错误
   - 解决方案：稍后重试或联系支持

## 性能优化

1. 合理设置 temperature 参数
2. 控制 max_tokens 以获得更快的响应
3. 使用多 API 代理实现负载均衡
4. 缓存常用查询结果

## 许可证

本 API 遵循 CSDN 的使用条款和许可证。
