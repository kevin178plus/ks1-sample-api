# JSON 解析错误诊断指南

## 问题描述
在 http://localhost:5000/debug 联调测试时收到错误：
```
Expecting value: line 1 column 1 (char 0)
```

## 问题原因
这是典型的 JSON 解析错误，说明期望收到 JSON 响应，但实际收到的是：
- 空响应（空字符串或无内容）
- HTML 错误页面（如 500 错误）
- 其他格式错误的响应
- 上游 API 返回了错误信息但不是 JSON 格式

## 诊断步骤

### 1. 重启服务以应用新的诊断日志
```bash
# 停止当前运行的服务（如果在运行）
# 然后重新启动
python multi_free_api_proxy/multi_free_api_proxy_v3_optimized.py
```

### 2. 在调试页面重现问题
访问 http://localhost:5000/debug，在"测试聊天"标签页发送一条消息。

### 3. 查看控制台输出
新的诊断日志会显示：
```
[诊断] {api_name} 上游响应状态码: 200
[诊断] {api_name} 上游响应Content-Type: application/json
[诊断] {api_name} 上游响应长度: 1234 字符
```

如果发生错误，会显示：
```
[错误] {api_name} JSON解析失败: Expecting value: line 1 column 1 (char 0)
[错误] {api_name} 原始响应 (前500字符): <实际返回的内容>
```

### 4. 根据诊断结果判断问题类型

#### 情况 A：上游返回空响应
```
[错误] {api_name} 上游返回空响应
```
**结论**：上游 AI 服务问题，可能服务不稳定或超时

#### 情况 B：上游返回 HTML 错误页面
```
[错误] {api_name} 原始响应: <!DOCTYPE html><html>...
```
**结论**：上游 AI 服务返回了 HTML 错误页面，可能是：
- 服务内部错误（500）
- 鉴权失败（401/403）
- 请求格式错误（400）

#### 情况 C：上游返回非 JSON 格式
```
[错误] {api_name} 原始响应: Some error message in plain text
```
**结论**：上游 AI 服务返回了纯文本错误信息，说明：
- 可能是 API 兼容性问题
- 需要检查该 API 的响应格式是否与 OpenAI 格式兼容

#### 情况 D：上游返回有效的 JSON
```
[请求] {api_name} 独立服务成功
```
**结论**：上游正常，问题可能在代码的其他部分

## 常见上游 AI 返回格式差异

### OpenAI 标准格式
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "回复内容"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 可能的兼容性问题
1. **缺少 choices 字段**：某些 AI 可能直接返回 content
2. **字段名不同**：可能是 `message` vs `messages`，`finish_reason` vs `stop_reason`
3. **嵌套结构不同**：可能是扁平结构而非嵌套
4. **错误响应格式**：可能返回 `error.message` 而非 JSON 对象

## 解决方案

### 如果是上游服务问题
1. 检查该 API 的服务状态
2. 在"API管理"标签页临时禁用该 API
3. 增加重试次数或超时时间

### 如果是兼容性问题
1. 检查该 API 的文档，确认响应格式
2. 可能需要为该特定 API 添加响应转换逻辑
3. 在 `config.py` 中配置该 API 的特殊参数

### 添加 API 特定响应处理
如果某个 API 需要特殊处理，可以在代码中添加：

```python
# 在 response.json() 调用之前
if api_name == "specific_api":
    # 特殊处理逻辑
    custom_result = parse_custom_response(response_text)
    result = custom_result
else:
    result = response.json()
```

## 调试技巧

### 1. 单独测试有问题的 API
```bash
cd free_api_test/free5
python test_api.py
```

### 2. 使用 curl 直接测试上游
```bash
curl -X POST https://api.example.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}'
```

### 3. 查看完整的响应内容
修改诊断日志中的 `response_text[:500]` 为 `response_text` 查看完整响应。

## 注意事项

1. **不要在生产环境打印完整响应**：可能包含敏感信息
2. **定期检查上游 API 文档**：格式可能随时间变化
3. **监控 API 成功率**：在调试页面的"统计信息"标签页查看
4. **合理设置权重**：对于经常出错的 API，可以降低权重或禁用

## 下一步

1. 应用新的诊断代码
2. 重启服务
3. 重现问题并查看日志
4. 根据日志内容确定具体问题
5. 如果是兼容性问题，提供具体的上游响应格式以便进一步修复

## 智能切换和黑名单机制

### 自动切换功能

当检测到格式错误（如 JSON 解析失败）时，系统会自动采取以下措施：

1. **立即切换**：不等待重试延迟，立即尝试下一个 API
2. **加入黑名单**：将出错的 API 临时加入黑名单（60秒）
3. **降低权重**：大幅降低该 API 的权重（-50）
4. **记录日志**：详细记录诊断信息和切换过程

### 日志示例

```
[请求] 发送到 free5 (尝试 1/3)
[诊断] free5 上游响应状态码: 200
[诊断] free5 上游响应Content-Type: text/html
[诊断] free5 上游响应长度: 256 字符
[错误] free5 JSON解析失败: Expecting value: line 1 column 1 (char 0)
[错误] free5 原始响应 (前500字符): <!DOCTYPE html><html><head><title>500 Internal Server Error</title></head>
[黑名单] free5 已加入临时黑名单 (60秒)
[权重] free5 权重自动减少: 100 -> 50 (减少: 50)
[请求] 格式错误 - 快速切换到下一个 API: Invalid JSON response from free5
[重试] 立即尝试下一个 API...
[选择] 可用 API 数量: 9/10
[请求] 发送到 free1 (尝试 2/3)
[请求] free1 独立服务成功
```

### 黑名单机制

**工作原理**：
- 检测到格式错误后，API 自动加入黑名单
- 黑名单持续时间为 60 秒
- 60 秒后自动从黑名单移除
- 在黑名单期间，该 API 不会被选中

**适用场景**：
- JSON 解析失败
- 上游返回非 JSON 格式
- 上游返回空响应

**不影响的情况**：
- 超时错误（仍会重试，但不会加入黑名单）
- HTTP 错误（仍会重试）
- 连接错误（仍会重试）

### 权重调整

**自动权重调整规则**：
- 格式错误：权重减少 50
- 成功响应：权重逐渐减少（避免过度使用）
- 权重不会低于最低限制（50）

**手动管理权重**：
```bash
# 查看所有 API 权重
curl http://localhost:5000/debug/api/weight

# 设置特定权重
curl -X POST http://localhost:5000/debug/api/weight \
  -H "Content-Type: application/json" \
  -d '{"api_name": "free5", "weight": 100}'

# 重置所有权重为默认值
curl -X POST http://localhost:5000/debug/api/weight/reset \
  -H "Content-Type: application/json"
```

### 优势和效果

**1. 快速恢复**：
- 遇到格式错误立即切换，不浪费时间
- 用户请求延迟最小化

**2. 智能规避**：
- 临时屏蔽不稳定的 API
- 减少重复错误的发生

**3. 自适应优化**：
- 根据表现自动调整权重
- 健康的 API 更容易被选中

**4. 易于监控**：
- 详细的日志输出
- 清晰的切换过程

### 常见问题

**Q: 黑名单会永久禁用 API 吗？**
A: 不会。黑名单是临时的，60 秒后自动移除。API 可以继续被使用。

**Q: 如果所有 API 都在黑名单中怎么办？**
A: 系统会使用原始的可用 API 列表，确保至少有一个 API 可以使用。

**Q: 可以修改黑名单持续时间吗？**
A: 可以。在 `app_state.py` 中修改 `failed_api_blacklist_duration` 参数。

**Q: 格式错误会重试多少次？**
A: 由 `MAX_RETRIES` 配置决定，默认为 3 次。每次格式错误都会切换到不同的 API。