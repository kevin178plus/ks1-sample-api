# CGC ChanCloud AI

## 概述

CGC ChanCloud AI 是一个提供 NVIDIA Nemotron 系列大模型服务的 API 平台，支持流式响应（SSE）。

## API 信息

### 官方网站
https://cgc.chancloud.com

### 支持的模型
- Nemotron-3-Super-120B-A12B (默认)

## 配置说明

### 环境变量配置
在 `.env` 文件中添加:
```
FREE14_API_KEY=你的 API_KEY
```

### config.py 配置
```python
TITLE_NAME = "CGC ChanCloud AI"
BASE_URL = "https://cgc.chancloud.com/cgc/api/public/ai/server"
MODEL_NAME = "Nemotron-3-Super-120B-A12B"
USE_PROXY = False
USE_SDK = False
DEFAULT_WEIGHT = 10
ENDPOINT = "/chat/stream"
MAX_TOKENS = 1024
```

## 使用示例

### curl 示例
```bash
curl https://cgc.chancloud.com/cgc/api/public/ai/server/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "Nemotron-3-Super-120B-A12B",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.5,
    "top_p": 1,
    "max_tokens": 1024,
    "stream": true
  }'
```

## 测试方法

### 快速测试
```bash
python test_api.py
```

### 在 multi_free_api_proxy 中使用
此 API 配置会被 `multi_free_api_proxy` 自动加载和检测。

1. 确保在 `.env` 中配置了 `FREE14_API_KEY`
2. 启动 multi_free_api_proxy
3. 系统会自动测试此 API 的可用性
4. 如果可用，会加入到轮换池中

## 注意事项

1. API 仅支持 SSE 流式响应
2. 需要使用 truststore 处理 SSL 证书
3. 默认权重较低，建议根据实际使用情况调整

## 更新日志

- 2026-03-23: 初始版本
