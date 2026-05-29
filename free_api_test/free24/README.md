# ModelScope API (free24)

## 概述
ModelScope（魔搭社区）是阿里云推出的 AI 模型服务平台，提供 6 万+ 开源模型的免费 API 推理服务。
完全兼容 OpenAI API 格式。

## API 信息

### 官方网站
https://www.modelscope.cn

### API 文档
https://www.modelscope.cn/docs/model-service/API-Inference/intro

### 支持模型
ModelScope 支持数千个模型的 API-Inference，包括但不限于：

- **Qwen/Qwen3.5-35B-A3B** (默认) — 通义千问最新开源版
- **Qwen/Qwen2.5-Coder-32B-Instruct** — 通义千问代码模型
- **Qwen/Qwen2.5-7B-Instruct** — 轻量级 7B 模型
- **ZhipuAI/GLM-4.7-Flash** — 智谱 GLM 闪速版

完整模型列表请访问：https://modelscope.cn/models?filter=inference_type

## 配置说明

### 获取 API Key
1. 访问 https://modelscope.cn 注册并登录
2. 进入个人中心 → 我的AccessToken → 创建 Token
3. 需绑定阿里云账号并完成实名认证
4. 复制 SDK Token

### 环境变量配置
在 `.env` 文件中添加:
```
FREE24_API_KEY=你的ModelScope SDK Token
```

### config.py 配置
```python
TITLE_NAME = "ModelScope (魔搭)"
BASE_URL = "https://api-inference.modelscope.cn/v1"
MODEL_NAME = "Qwen/Qwen3.5-35B-A3B"
USE_PROXY = False
USE_SDK = False
DEFAULT_WEIGHT = 90
```

## 使用示例

### Python 示例
```python
import requests

url = "https://api-inference.modelscope.cn/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
payload = {
    "model": "Qwen/Qwen3.5-35B-A3B",
    "messages": [{"role": "user", "content": "Hello!"}]
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### curl 示例
```bash
curl -X POST https://api-inference.modelscope.cn/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.5-35B-A3B",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 测试方法

### 快速测试
```bash
cd free_api_test/free24
python test_api.py
```

### 在 multi_free_api_proxy 中使用
此 API 配置会被 `multi_free_api_proxy` 自动加载和检测。
1. 确保在 `.env` 中配置了 `FREE24_API_KEY`
2. 启动 multi_free_api_proxy
3. 系统会自动测试此 API 的可用性

## 注意事项
1. 需注册并绑定阿里云账号、完成实名认证后才可使用 API-Inference
2. 免费额度：每日 2000 次调用（全部模型共用），每 24 小时重置
3. 超出限制返回 429 错误
4. 国内服务，无需代理
5. 模型 ID 格式为 ModelScope 上的模型路径（如 `Qwen/Qwen3.5-35B-A3B`）

## 更新日志
- 2026-05-27: 初始版本
