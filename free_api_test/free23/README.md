# 小米 MiMo API (free23)

## 概述
小米 MiMo 大模型 API 开放平台，提供高性能大模型推理服务，支持文本对话、深度思考、工具调用、TTS 语音合成等能力。
完全兼容 OpenAI API 格式。

## API 信息

### 官方网站
https://platform.xiaomimimo.com

### API 文档
https://platform.xiaomimimo.com/docs

### 支持模型
- **mimo-v2.5-pro** (默认) — 最新 Pro 系列，深度思考+工具调用
- **mimo-v2.5-tts** — 语音合成（声音克隆+精细指令控制）
- **mimo-v2-pro** — 标准旗舰版
- **mimo-v2-flash** — 轻量快速版

完整模型列表请访问：https://platform.xiaomimimo.com/docs/en-US/quick-start/model

## 配置说明

### 获取 API Key
1. 访问 https://platform.xiaomimimo.com 使用小米账号登录
2. 进入 Console → API Keys → 创建 API Key
3. 复制并妥善保管 API Key

### 环境变量配置
在 `.env` 文件中添加:
```
FREE23_API_KEY=你的API Key
```

### config.py 配置
```python
TITLE_NAME = "小米 MiMo"
BASE_URL = "https://api.xiaomimimo.com/v1"
MODEL_NAME = "mimo-v2.5-pro"
USE_PROXY = False
USE_SDK = False
DEFAULT_WEIGHT = 100
```

## 使用示例

### Python 示例
```python
import requests

url = "https://api.xiaomimimo.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "model": "mimo-v2.5-pro",
    "messages": [{"role": "user", "content": "Hello!"}]
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### curl 示例
```bash
curl -X POST https://api.xiaomimimo.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mimo-v2.5-pro",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 测试方法

### 快速测试
```bash
cd free_api_test/free23
python test_api.py
```

### 在 multi_free_api_proxy 中使用
此 API 配置会被 `multi_free_api_proxy` 自动加载和检测。
1. 确保在 `.env` 中配置了 `FREE23_API_KEY`
2. 启动 multi_free_api_proxy
3. 系统会自动测试此 API 的可用性

## 注意事项
1. 需要小米账号登录才能获取 API Key
2. Token Plan 可购买获得调用额度，新用户有免费额度
3. 国内服务，无需代理，可直接访问
4. 支持 `api-key` 和 `Authorization: Bearer` 两种鉴权方式
5. 深度思考模式会返回 `reasoning_content` 字段

## 更新日志
- 2026-05-27: 初始版本
