# SenseNova API (free22)

## 概述
商汤科技 SenseNova 大模型 API 服务平台，提供多种大模型调用能力。
完全兼容 OpenAI API 格式，可直接替换 OpenAI SDK 的 base_url。

## API 信息

### 官方网站
https://platform.sensenova.cn

### API 文档
https://platform.sensenova.cn/docs

### 支持模型
- **sensenova-6.7-flash-lite** (默认) — 轻量多模态，256K上下文，1500次/5h免费额度
- **sensenova-u1-fast** — 信息图生成专用，1500次/5h
- **deepseek-v4-flash** — DeepSeek 高性能对话，256K上下文，工具调用，150次/5h

完整模型列表请访问：https://platform.sensenova.cn/models

## 配置说明

### 获取 API Key
1. 访问 https://platform.sensenova.cn/console 注册并完成实名认证
2. 进入控制台 → 管理中心 → API-Key 管理 → 创建 API-Key
3. 创建成功后**立即复制并妥善保管**（仅创建时完整显示一次）

### 环境变量配置
在 `.env` 文件中添加:
```
FREE22_API_KEY=你的sk-开头的API Key
```

### config.py 配置
```python
TITLE_NAME = "SenseNova"
BASE_URL = "https://token.sensenova.cn/v1"
MODEL_NAME = "sensenova-6.7-flash-lite"
USE_PROXY = False
USE_SDK = False
DEFAULT_WEIGHT = 100
```

## 使用示例

### Python 示例
```python
import requests

url = "https://token.sensenova.cn/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "model": "sensenova-6.7-flash-lite",
    "messages": [{"role": "user", "content": "Hello!"}]
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### curl 示例
```bash
curl -X POST https://token.sensenova.cn/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sensenova-6.7-flash-lite",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 测试方法

### 快速测试
```bash
cd free_api_test/free22
python test_api.py
```

### 在 multi_free_api_proxy 中使用
此 API 配置会被 `multi_free_api_proxy` 自动加载和检测。
1. 确保在 `.env` 中配置了 `FREE22_API_KEY`
2. 启动 multi_free_api_proxy
3. 系统会自动测试此 API 的可用性

## 注意事项
1. 需要注册并完成实名认证才能获取 API Key
2. 不同模型有各自的免费调用次数限制（每5小时）
3. 国内服务，无需代理，可直接访问
4. API Key 仅在创建时完整显示一次，务必及时保存

## 更新日志
- 2026-05-27: 初始版本
