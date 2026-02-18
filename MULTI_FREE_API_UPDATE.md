# 多Free API代理服务更新说明

## 更新内容

### 1. 修改了.env文件
添加了以下Free API Keys:
```
FREE1_API_KEY=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
FREE2_API_KEY=sk-RJeQTUufTH2oUcdLLyOIMZbxFQNwVZdi622xyZaCEJV7ltLt
FREE3_API_KEY=sk-t76OXjTTXmPRzpNj8aF6F5F0508b488fB087A51c760e7dD8
```

### 2. 修改了free*/test_api.py文件
修改了free1、free2、free3目录下的test_api.py文件，使其从.env读取API Key:
```python
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量读取API Key
API_KEY = os.getenv("FREE1_API_KEY")  # 或 FREE2_API_KEY, FREE3_API_KEY
if not API_KEY:
    raise ValueError("FREE1_API_KEY not found in .env file")
```

### 3. 修改了multi_free_api_proxy.py
主要修改:
1. 从.env加载Free API Keys
2. 为每个API指定特定的模型:
   - free1: openrouter/free
   - free2: gpt-3.5-turbo
   - free3: gpt-3.5-turbo
3. 忽略原始请求中的model参数，只使用API配置的模型

## 使用方法

1. 确保已安装python-dotenv:
```bash
pip install python-dotenv
```

2. 启动服务:
```bash
python multi_free_api_proxy_v2.py
```

3. 服务会自动:
   - 检测free1、free2、free3三个API
   - 测试这些API是否可用
   - 轮换使用这些可用的API
   - 每个API使用其配置的特定模型

## API模型配置

| API | 模型 | 说明 |
|-----|------|------|
| free1 | openrouter/free | OpenRouter免费模型 |
| free2 | gpt-3.5-turbo | ChatAnywhere API |
| free3 | gpt-3.5-turbo | Free ChatGPT API |

## 注意事项

1. 所有API Key都存储在.env文件中，便于管理和保护
2. 每个API使用其特定的模型，忽略客户端请求的model参数
3. 服务会轮换使用这三个API，实现负载均衡
4. 定期(每5分钟)重新测试所有API的可用性
