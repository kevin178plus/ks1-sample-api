# Free API Test - NVIDIA API

本项目用于测试 NVIDIA API 的调用，特别是 z-ai/glm4.7 模型。

## 目录结构

```
free7/
├── README.md           # 本文件
├── config.py          # API 配置文件
├── demo.py            # 简单的 API 调用示例（使用 requests）
├── demo2.py           # 使用 OpenAI SDK 的示例
├── test_api.py        # 完整的 API 测试脚本
├── debug_test.py      # 调试测试脚本（测试多种配置）
├── ask.txt            # 测试问题文件
├── test_result.txt    # API 返回结果
├── .env               # 环境变量配置
└── _nvidia-API.txt    # API 笔记
```

## 配置说明

### 环境变量 (.env)

在 `.env` 文件中配置以下变量：

```env
FREE7_API_KEY=nvapi-xxxxx  # NVIDIA API Key
HTTP_PROXY=http://127.0.0.1:7897  # 代理地址（可选）
```

### config.py

```python
API_KEY = os.getenv("FREE7_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/"
MODEL_NAME = "z-ai/glm4.7"
```

## API 数据结构

### 请求格式

```json
{
  "model": "z-ai/glm4.7",
  "messages": [
    {"role": "user", "content": "你的问题"}
  ],
  "max_tokens": 1024,
  "temperature": 0.20,
  "top_p": 1.00,
  "stream": false,
  "chat_template_kwargs": {
    "thinking": false
  }
}
```

### 响应格式

```json
{
  "id": "694398f8e5a44be794a5b52760eb4fd7",
  "object": "chat.completion",
  "created": 1771683519,
  "model": "z-ai/glm4.7",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,  // 注意：可能为 null
        "reasoning_content": "实际的回答内容",  // 推理内容
        "tool_calls": null
      },
      "logprobs": null,
      "finish_reason": "length",
      "matched_stop": null
    }
  ],
  "usage": {
    "prompt_tokens": 393,
    "total_tokens": 1417,
    "completion_tokens": 1024,
    "prompt_tokens_details": null,
    "reasoning_tokens": 0
  },
  "metadata": {
    "weight_version": "default"
  }
}
```

### 重要说明

1. **content 和 reasoning_content 的区别**：
   - `content`：模型的最终输出内容（答案）
   - `reasoning_content`：模型的思考过程（推理链）

2. **chat_template_kwargs 参数的影响**：
   - `thinking: False`：返回 content 和 reasoning_content，content 包含最终答案
   - `thinking: True`：返回 content 和 reasoning_content，content 包含最终答案
   - `enable_thinking: True, clear_thinking: False`：启用思考模式，不清除思考内容
   - 不设置 chat_template_kwargs：默认行为

3. **处理逻辑**：
   - 优先使用 `content` 字段（这是最终答案）
   - 如果 `content` 为 `null`，则检查 `reasoning_content` 字段
   - 注意：`reasoning_content` 是思考过程，不是最终答案
   - 如果两者都为 `null`，则视为错误

4. **finish_reason**：
   - `length`: 达到 max_tokens 限制（内容可能被截断）
   - `stop`: 正常完成
   - 其他值表示特殊情况

5. **max_tokens 建议**：
   - 简单问题：1024-2048
   - 复杂问题：4096-8192
   - 注意：如果设置为 1024，可能导致 reasoning_content 或 content 被截断

6. **流式输出**：
   - 使用 OpenAI SDK 并设置 `stream=True`
   - 同时监听 `reasoning_content` 和 `content` 字段
   - 参考 demo2.py 和 demo3.py 的实现

## 使用示例

### 1. 使用 test_api.py

```bash
python test_api.py
```

这个脚本会：
- 从 `ask.txt` 读取问题
- 调用 NVIDIA API
- 将结果保存到 `test_result.txt`

### 2. 使用 demo.py

```bash
python demo.py
```

简单的 API 调用示例，直接在代码中配置参数。

### 3. 使用 demo2.py

```bash
python demo2.py
```

使用 OpenAI SDK 的示例，支持流式输出。

### 4. 使用 debug_test.py

```bash
python debug_test.py
```

测试多种配置组合，包括：
- 使用/不使用代理
- thinking=True/False
- 不同的 API Key

## 常见问题

### 1. content 和 reasoning_content 有什么区别？

- **content**：模型的最终输出内容（答案）
- **reasoning_content**：模型的思考过程（推理链）

**重要**：`reasoning_content` 是思考过程，不是最终答案！它包含了模型分析问题、拆解元素、头脑风暴、起草内容等步骤。如果你需要的是最终答案，应该使用 `content` 字段。

### 2. 为什么 content 为 null？

在以下情况下，`content` 可能为 `null`：
- max_tokens 设置太小，导致还没生成最终答案就达到了限制
- 模型配置问题
- 某些特定参数组合

**建议**：
- 增大 max_tokens（如 2048 或 4096）
- 检查 chat_template_kwargs 参数
- 优先使用 `content`，如果为 `null` 再检查 `reasoning_content`

### 3. 如何处理流式输出？

参考 `demo2.py` 和 `demo3.py`：
- 使用 OpenAI SDK 并设置 `stream=True`
- 同时监听 `reasoning_content` 和 `content` 字段
- 示例代码：
  ```python
  for chunk in completion:
    delta = chunk.choices[0].delta
    reasoning = getattr(delta, "reasoning_content", None)
    if reasoning:
      print(reasoning, end="")
    if getattr(delta, "content", None) is not None:
      print(delta.content, end="")
  ```

### 4. 如何选择 max_tokens？

根据问题复杂度选择：
- 简单问题：1024-2048
- 复杂问题：4096-8192
- 需要详细推理：8192+

**注意**：max_tokens 太小可能导致：
- reasoning_content 被截断
- content 为 null 或不完整
- finish_reason 为 "length"

### 5. 代理配置

如果需要使用代理，在 `.env` 文件中设置 `HTTP_PROXY` 环境变量。`test_api.py` 会自动读取并使用。

示例：
```env
HTTP_PROXY=http://127.0.0.1:7897
```

## 注意事项

1. API Key 需要保密，不要提交到版本控制系统
2. 代理地址需要根据实际情况配置
3. max_tokens 参数影响返回内容的长度
4. temperature 参数控制输出的随机性（0.0-1.0）
5. 注意 API 的调用频率限制

## 更新日志

- 2026-02-21: 添加多角度测试结果，明确 content 和 reasoning_content 的区别
- 2026-02-21: 更新常见问题，添加关于 reasoning_content 的详细说明
- 2026-02-21: 添加 max_tokens 建议和流式输出示例
- 2026-02-20: 添加数据结构说明和 content/reasoning_content 处理逻辑
- 2026-02-20: 修复 test_api.py 处理 reasoning_content 的问题
