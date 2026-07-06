# Agnes AI API (free25)

## 概述
Agnes AI 是一个由 Agnes AI 平台提供的免费 AI API 服务，支持文本生成和图像生成，完全兼容 OpenAI API 格式。

## API 信息

### 官方网站
https://platform.agnes-ai.com

### API Key 获取
https://platform.agnes-ai.com/settings/apiKeys

### 支持的模型

| 模型名称 | 类型 | 上下文窗口 | 价格 |
|----------|------|-----------|------|
| agnes-2.0-flash | 文本 | 512K | $0 / 1M tokens |
| agnes-image-2.1-flash | 图像 | - | $0 / 张 |

### agnes-2.0-flash（文本模型）
- API Endpoint: `POST /v1/chat/completions`
- 上下文窗口: 512K tokens
- 当前价格: 输入/输出 Token 均为免费

### agnes-image-2.1-flash（图像模型）
- API Endpoint: `POST /v1/images/generations`
- 核心优化: 高信息密度图像、复杂视觉细节和语义对齐
- 当前价格: 生成图像免费

## 配置说明

### 获取 API Key
1. 访问 https://platform.agnes-ai.com/settings/apiKeys
2. 注册并登录账号
3. 创建 API Key

### 环境变量配置
在 `.env` 文件中添加:
```
FREE25_API_KEY=sk-xxxxx
```

### config.py 配置
```python
TITLE_NAME = "Agnes AI"
BASE_URL = "https://apihub.agnes-ai.com/v1"
MODEL_NAME = "agnes-2.0-flash"
USE_PROXY = False
USE_SDK = False
DEFAULT_WEIGHT = 10
```

## 使用示例

### Python 示例
```python
import requests

url = "https://apihub.agnes-ai.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "model": "agnes-2.0-flash",
    "messages": [{"role": "user", "content": "Hello!"}]
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### curl 示例
```bash
curl -X POST https://apihub.agnes-ai.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agnes-2.0-flash",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 测试方法

### 快速测试
```bash
cd free_api_test/free25
python test_api.py
```

### 在 multi_free_api_proxy 中使用
此 API 配置会被 `multi_free_api_proxy` 自动加载和检测。
1. 确保在 `.env` 中配置了 `FREE25_API_KEY`
2. 启动 multi_free_api_proxy
3. 系统会自动测试此 API 的可用性

## 注意事项
1. 当前服务完全免费，无调用限制
2. 国内服务，无需代理
3. agnes-2.0-flash 支持 512K 超长上下文
4. agnes-image-2.1-flash 专门优化图像生成能力

## 更新日志
- 2026-07-06: 初始版本