# friendli.ai API

## 简介
friendli.ai 是一家提供高性能大语言模型服务的 AI 公司，其 API 兼容 OpenAI SDK 格式。

## API 信息
- Base URL: `https://api.friendli.ai/serverless/v1`
- 认证方式: Bearer Token

## 可用模型
| 模型名称 | 默认权重 | 说明 |
|---------|---------|------|
| meta-llama/Llama-3.3-70B-Instruct | 5 (38.5%) | 新增：Meta 大模型 |
| Qwen/Qwen3-235B-A22B-Instruct-2507 | 4 (30.8%) | 新增：阿里 Qwen3 大模型 |
| MiniMaxAI/MiniMax-M2.5 | 3 (23.1%) | 默认首选模型 |
| zai-org/GLM-4.7 | 2 (15.4%) | 备选模型 |
| zai-org/GLM-5 | 1 (7.7%) | 备选模型 |

**权重说明**: 
- 5个模型的权重比例为 5:4:3:2:1
- 在15次访问中，预期分布约为：第1个5次，第2个4次，第3个3次，第4个2次，第5个1次
- 可通过 `config.py` 中的 `AVAILABLE_MODELS` 列表调整模型顺序和数量

## API Key
需要设置环境变量：
- `FRIENDLI_TOKEN`: API 认证令牌
- `FRIENDLI_TEAM_ID`: 团队 ID（可选）

## 文件说明

| 文件 | 说明 |
|-----|------|
| `config.py` | 配置文件，包含模型列表、权重分配函数 |
| `test_api.py` | API 测试脚本，支持分权制模型选择 |
| `test_api_proxy.py` | 代理测试脚本，强制使用代理访问 |
| `local_api_proxy.py` | 本地 API 代理服务（待修改） |

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

# 运行直接访问测试
python test_api.py

# 运行代理测试
python test_api_proxy.py

# 测试权重分配
python config.py
```

## 注意事项
1. Friendli API 兼容 OpenAI SDK 格式
2. 需要有效的 API Key 才能使用
3. API 有调用频率限制，请参考官方文档
4. 模型选择采用分权制，按列表顺序权重递减
