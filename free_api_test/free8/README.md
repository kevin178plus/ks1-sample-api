# friendli.ai API

## 简介
friendli.ai 是一家提供高性能大语言模型服务的 AI 公司，其 API 兼容 OpenAI SDK 格式。

## 架构说明
free8 以**独立服务**形式运行，提供权重模型选择功能：
- **服务端口**: 5008
- **服务文件**: `friendli_service.py`
- **主服务路由**: 通过主服务自动路由到独立服务
- **直接访问**: 也可以直接调用独立服务的 API

## API 信息
- Base URL: `https://api.friendli.ai/serverless/v1`
- 认证方式: Bearer Token

## 可用模型
| 模型名称 | 默认权重 | 说明 |
|---------|---------|------|
| Qwen/Qwen3-235B-A22B-Instruct-2507 | 4 (40%) | 默认首选模型 |
| MiniMaxAI/MiniMax-M2.5 | 3 (30%) | 备选模型 |
| zai-org/GLM-4.7 | 2 (20%) | 备选模型 |
| zai-org/GLM-5 | 1 (10%) | 备选模型 |

**权重说明**:
- 4个模型的权重比例为 4:3:2:1
- 独立服务会自动按权重随机选择模型
- 可通过 `config.py` 中的 `AVAILABLE_MODELS` 列表调整模型顺序和数量

## API Key
需要设置环境变量（在 `.env` 文件中）：
- `FREE8_API_KEY`: API 认证令牌（用于独立服务）

## 文件说明

| 文件 | 说明 |
|-----|------|
| `config.py` | 配置文件，包含模型列表、权重分配函数 |
| `friendli_service.py` | 独立服务，提供权重模型选择功能（端口 5008） |
| `test_api.py` | API 测试脚本，支持权重模型选择 |

## 使用示例

### cURL 示例
```bash
curl -X POST https://api.friendli.ai/serverless/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Friendli-Team: $FRIENDLI_TEAM_ID" \
  -H "Authorization: Bearer $FRIENDLI_TOKEN" \
  -d '{
    "model": "zai-org/GLM-5",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

### Python 示例
```python
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

### 分权制模型选择示例
```python
from config import select_model_by_weight, get_weight_distribution

# 查看权重分布
distribution = get_weight_distribution()
for model, info in distribution.items():
    print(f"{model}: 权重={info['weight']}, 占比={info['percentage']}%")

# 按权重随机选择模型
model = select_model_by_weight()
print(f"选中的模型: {model}")
```

## 运行测试

```bash
# 进入目录
cd free_api_test/free8

# 启动独立服务
python friendli_service.py

# 在另一个终端运行测试
python test_api.py

# 测试权重分配
python config.py
```

## 独立服务端点

启动独立服务后，可以访问以下端点：

```bash
# 健康检查
curl http://localhost:5008/health

# 列出模型
curl http://localhost:5008/v1/models

# 统计信息
curl http://localhost:5008/v1/stats

# 聊天完成（自动权重选择）
curl -X POST http://localhost:5008/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

## 调试信息

独立服务的响应中包含 `_debug` 字段，显示：
- 选中的模型
- 权重分布
- 时间戳

示例：
```json
{
  "id": "chatcmpl-xxx",
  "choices": [...],
  "_debug": {
    "selected_model": "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "weight_distribution": {
      "Qwen/Qwen3-235B-A22B-Instruct-2507": 4,
      "MiniMaxAI/MiniMax-M2.5": 3,
      "zai-org/GLM-4.7": 2,
      "zai-org/GLM-5": 1
    },
    "timestamp": "2026-03-05T10:30:00"
  }
}
```
```

## 注意事项
1. Friendli API 兼容 OpenAI SDK 格式
2. 需要有效的 API Key 才能使用
3. API 有调用频率限制，请参考官方文档
4. 模型选择采用分权制，按列表顺序权重递减
