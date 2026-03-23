# {API 名称}

## 概述
{简要描述 API 提供商和服务}

## API 信息

### 官方网站
{API 提供商官网链接}

### API 文档
{API 文档链接}

### 支持的模型
{列出主要支持的模型，例如:}
- model-name-1 (描述)
- model-name-2 (描述)
- ...

完整模型列表请访问：{模型列表页面链接}

## 配置说明

### 获取API Key
1. 访问 {注册/登录链接}
2. {步骤 2}
3. {步骤 3}
4. 复制 API Key

### 环境变量配置
在 `.env` 文件中添加:
```
FREE{编号}_API_KEY=你的 API_KEY
```

### config.py 配置
```python
TITLE_NAME = "{显示名称}"
BASE_URL = "{API 基础 URL}"
MODEL_NAME = "{默认模型名称}"
USE_PROXY = {True/False}
USE_SDK = {True/False}
DEFAULT_WEIGHT = {权重值}
```

## 使用示例

### Python 示例
```python
import requests
import json

url = "{BASE_URL}/chat/completions"

headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

payload = {
    "model": "{MODEL_NAME}",
    "messages": [
        {
            "role": "user",
            "content": "Hello!"
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### curl 示例
```bash
curl -X POST {BASE_URL}/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "{MODEL_NAME}",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

## 测试方法

### 快速测试
```bash
cd free{编号}
python test_api.py
```

### 在 multi_free_api_proxy 中使用
此 API 配置会被 `multi_free_api_proxy` 自动加载和检测。

1. 确保在 `.env` 中配置了 `FREE{编号}_API_KEY`
2. 启动 multi_free_api_proxy
3. 系统会自动测试此 API 的可用性
4. 如果可用，会加入到轮换池中

## 注意事项
1. {注意事项 1}
2. {注意事项 2}
3. {注意事项 3}

## 常见问题

### Q: {常见问题 1}
A: {答案}

### Q: {常见问题 2}
A: {答案}

## 更新日志
- YYYY-MM-DD: 初始版本
- YYYY-MM-DD: {更新内容}
