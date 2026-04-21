# iFlow SDK API

## ⚠️ 服务状态：已停用

> **注意**：iFlow SDK 服务已于 2026 年 3 月停用，此 API 配置已被禁用。
> 如需启用，请在 `.env` 文件中取消注释 `FREE5_API_KEY` 配置。

## 概述

iFlow SDK 是一个基于 Python 的异步 AI 查询 SDK，提供简单易用的接口来访问 AI 模型服务。

## 架构说明

free5 以**独立服务**形式运行，提供 iFlow SDK 的异步查询能力：
- **服务端口**: 5005
- **服务文件**: `iflow_api_proxy.py`
- **主服务路由**: 通过主服务自动路由到独立服务
- **直接访问**: 也可以直接调用独立服务的 API

## 特性

- 异步查询支持
- OpenAI API 兼容格式
- 自动事件循环管理
- 简单的查询接口

## 安装

```bash
pip install iflow-sdk
```

## 使用示例

### 基础查询

```python
from iflow_sdk import query
import asyncio

async def main():
    response = await query("法国的首都是哪里？")
    print(response)  # 输出：法国的首都是巴黎。

asyncio.run(main())
```

### 启动独立服务

本项目提供了 `iflow_api_proxy.py`，可以将 iFlow SDK 封装为 OpenAI 兼容的独立 API 服务：

```bash
cd free_api_test/free5
python iflow_api_proxy.py
```

服务将提供以下端点（端口 5005）：

- `POST /v1/chat/completions` - 聊天完成端点
- `GET /v1/models` - 列出可用模型
- `GET /health` - 健康检查

### 请求示例

```bash
curl -X POST http://localhost:5000/v1/chat/completions   -H "Content-Type: application/json"   -d '{
    "model": "iflow",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## 配置

### 环境变量

在 `.env` 文件中配置：

```properties
# 调试模式（可选）
DEBUG_MODE=true

# 缓存目录（可选）
CACHE_DIR=./cache

# 最大并发请求数（可选，默认5）
MAX_CONCURRENT_REQUESTS=5
```

### 调试模式

创建 `DEBUG_MODE.txt` 文件启用调试模式：

```bash
touch DEBUG_MODE.txt
```

调试模式下会记录所有请求和响应到缓存目录。

## 集成到多 API 代理

iFlow API (free5) 作为独立服务运行，可以通过主服务自动路由使用。

### 配置方法

1. 在 `.env` 文件中添加：
```properties
FREE5_API_KEY=any_value  # iFlow SDK 不需要 API Key，但需要设置此变量
```

2. 确保 iflow-sdk 已安装：
```bash
pip install iflow-sdk
```

3. 启动所有服务：
```bash
# 一键启动所有服务（推荐）
start_all_services.bat

# 或手动启动
cd free_api_test/free5 && python iflow_api_proxy.py  # 启动 free5 服务
cd ../multi_free_api_proxy && python multi_free_api_proxy_v3.py  # 启动主服务
```

### 工作原理

- 主服务检测到 free5 的请求时，自动路由到 `http://localhost:5005/v1/chat/completions`
- 独立服务处理请求并返回结果
- 如果独立服务未启动，主服务会自动跳过 free5

## 注意事项

1. iFlow SDK 使用异步查询，需要正确的事件循环管理
2. API 代理服务会自动处理事件循环
3. 免费使用可能有调用频率限制
4. 建议在生产环境中监控使用情况

## 错误处理

常见错误及解决方案：

1. **ImportError: No module named 'iflow_sdk'**
   - 解决方案：安装 iflow-sdk (`pip install iflow-sdk`)

2. **Event loop is closed**
   - 解决方案：确保正确管理事件循环，或使用提供的 API 代理服务

3. **连接超时**
   - 解决方案：检查网络连接，或增加超时时间

## 性能优化

1. 使用异步查询提高并发性能
2. 合理设置并发请求数
3. 启用调试模式监控性能指标
4. 使用多 API 代理实现负载均衡

## 许可证

本 SDK 遵循其原始许可证。
