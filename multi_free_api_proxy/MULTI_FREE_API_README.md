# 多Free API代理服务

## 概述

多Free API代理服务是一个能够自动检测、测试和轮换使用多个Free API的代理服务。它会自动检测`free_api_test`目录下的所有Free API(如free2、free3等),并在启动时测试这些API是否可用。如果API可用,则将其加入服务队列,收到请求时轮换使用这些可用的free API。

## 功能特性

1. **自动检测**: 自动检测`free_api_test`目录下的所有Free API
2. **启动测试**: 启动时测试所有Free API是否可用
3. **轮换使用**: 收到请求时轮换使用可用的Free API
4. **连续失败标记**: API连续失败3次后自动标记为无效，成功后自动恢复
5. **错误重试**: 支持请求失败时自动重试
6. **并发控制**: 支持并发请求控制
7. **调试模式**: 支持调试模式,记录请求和响应，提供Web调试面板
8. **健康检查**: 提供健康检查端点
9. **自动模型选择**: 忽略原始请求中的model参数,自动使用每个API支持的第一个模型
10. **SDK 支持**: 支持使用 SDK 调用 API (如 free5 使用 iflow SDK)
11. **统一接口**: 所有 API 提供统一的 OpenAI 兼容接口

## 安装

### 依赖项

- Python 3.7+
- Flask
- requests
- watchdog
- iflow-sdk (用于 free5)

### 安装依赖

```bash
pip install flask requests watchdog iflow-sdk
```

## 配置

### 环境变量

创建`.env`文件,配置以下环境变量:

```properties
# 服务端口(可选,默认5000)
PORT=5000

# 缓存目录(可选,用于调试模式)
CACHE_DIR=./cache

# HTTP代理(可选)
HTTP_PROXY=http://proxy.example.com:8080

# 最大并发请求数(可选,默认5)
MAX_CONCURRENT_REQUESTS=5

# Free API 配置
FREE1_API_KEY=your_openrouter_api_key
FREE2_API_KEY=your_chatanywhere_api_key
FREE3_API_KEY=your_free_v36_api_key
FREE4_API_KEY=your_mistral_api_key
FREE5_API_KEY=your_iflow_api_key  # 可选，free5 使用 iflow SDK
FREE6_API_KEY=your_csdn_api_key
```

### Free API配置

Free API的配置存储在`free_api_test`目录下的各个子目录中,如`free2`、`free3`等。每个子目录应包含:

1. `test_api.py`文件,其中包含API的配置信息(API_KEY和BASE_URL)
2. README文件(README.md、readme.txt或README.txt),其中包含支持的模型列表

示例`free2/test_api.py`:

```python
API_KEY = "sk-xxxxxxxxxxxx"
BASE_URL = "https://api.example.com"
```

或者使用openai库格式:

```python
import openai
openai.api_key = "sk-xxxxxxxxxxxx"
openai.base_url = "https://api.example.com/v1/"
```

注意: 如果base_url以`/v1/`结尾,服务会自动去掉`/v1/`部分

示例`free2/README.md`:

```markdown
# Free API

## 支持的模型
- gpt-3.5-turbo
- gpt-4o-mini
- deepseek-v3
```

### 模型选择机制

服务会自动从每个API的README文件中提取支持的模型列表,并在处理请求时:

1. **忽略原始请求中的model参数**: 无论客户端请求什么模型,服务都会使用API支持的第一个模型
2. **自动选择模型**: 每个API使用其支持的第一个模型进行测试和请求处理
3. **模型轮换**: 当请求轮换到不同的API时,会自动使用该API支持的模型

例如:
- free2 API支持[gpt-3.5-turbo, gpt-4o-mini],则使用gpt-3.5-turbo
- free3 API支持[gpt-4o-mini, gpt-3.5-turbo-0125],则使用gpt-4o-mini

## 使用

### 启动服务

Windows:
```bash
start_multi_free_api.bat        # 标准版本
start_multi_free_api_v3.bat     # V3版本(从.env读取配置)
```

Linux/Mac:
```bash
python multi_free_api_proxy.py       # 标准版本
python multi_free_api_proxy_v3.py    # V3版本
```

### API端点

#### 聊天完成

**端点**: `POST /v1/chat/completions`

**请求示例**:
```bash
curl -X POST http://localhost:5000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

#### 列出模型

**端点**: `GET /v1/models`

**请求示例**:
```bash
curl http://localhost:5000/v1/models
```

#### 健康检查

**端点**: `GET /health`

**请求示例**:
```bash
curl http://localhost:5000/health
```

#### 上游API状态

**端点**: `GET /health/upstream`

**请求示例**:
```bash
curl http://localhost:5000/health/upstream
```

## 调试模式

### 启用调试模式

在项目根目录创建一个名为`DEBUG_MODE.txt`的空文件:

```bash
touch DEBUG_MODE.txt
```

### 调试面板

启用调试模式后，访问 `http://localhost:5000/debug` 可以查看Web调试面板，包含:

- **统计信息**: 总调用次数、成功/失败/超时/重试计数
- **API状态**: 所有Free API的可用状态、成功/失败次数
- **测试聊天**: 直接在页面上测试API功能

### 调试API端点

#### 调试统计

**端点**: `GET /debug/stats`

**请求示例**:
```bash
curl http://localhost:5000/debug/stats
```

#### API状态

**端点**: `GET /debug/apis`

**请求示例**:
```bash
curl http://localhost:5000/debug/apis
```

#### 并发状态

**端点**: `GET /debug/concurrency`

**请求示例**:
```bash
curl http://localhost:5000/debug/concurrency
```

## 工作原理

1. **启动阶段**:
   - 检测`free_api_test`目录下的所有Free API
   - 测试每个Free API是否可用
   - 将可用的API加入服务队列

2. **请求处理**:
   - 从服务队列中获取下一个可用的API
   - 使用该API处理请求
   - 将该API移到队列末尾,实现轮换

3. **API状态管理**:
   - 每个API维护一个连续失败计数器
   - 请求成功时重置计数器
   - 连续失败3次后自动标记为无效并从可用列表移除
   - 被移除的API在下次成功后会自动恢复

## 故障排除

### 服务无法启动

1. 检查端口是否被占用
2. 检查Python依赖是否已安装
3. 检查`free_api_test`目录是否存在

### API不可用

1. 检查API_KEY是否正确
2. 检查BASE_URL是否正确
3. 检查网络连接是否正常
4. 查看日志了解详细错误信息
5. 访问调试面板查看API状态

### 请求失败

1. 检查请求格式是否正确
2. 检查是否有可用的API
3. 查看日志了解详细错误信息
4. 检查API是否被标记为无效（连续失败3次）

## 扩展

### 添加 HTTP API

要添加新的 HTTP Free API,只需在`free_api_test`目录下创建一个新的子目录,并在其中创建一个`test_api.py`文件,包含API的配置信息。服务会在下次启动时自动检测并测试新的API。

示例`free7/test_api.py`:

```python
API_KEY = "sk-xxxxxxxxxxxx"
BASE_URL = "https://api.example.com"
```

### 添加 SDK API

要添加使用 SDK 的 Free API,需要:

1. 在`multi_free_api_proxy_v3.py`中导入 SDK
2. 在`load_api_configs`函数中添加 API 配置,设置`use_sdk: True`
3. 在`test_api_startup`函数中添加 SDK 测试逻辑
4. 在`execute_with_free_api`函数中添加 SDK 调用逻辑

示例 (free5 使用 iflow SDK):

```python
# 1. 导入 SDK
try:
    from iflow_sdk import query as iflow_query
    IFLOW_SDK_AVAILABLE = True
except ImportError:
    IFLOW_SDK_AVAILABLE = False

# 2. 添加 API 配置
"free5": {
    "name": "free5",
    "api_key": FREE5_API_KEY,
    "base_url": "iflow",
    "model": "iflow",
    "use_proxy": False,
    "use_sdk": True  # 标记使用 SDK
}

# 3. 在 execute_with_free_api 中处理 SDK 调用
if use_sdk:
    # 使用 SDK 调用
    response_text = loop.run_until_complete(iflow_query(user_message))
    # 构建 OpenAI 兼容响应
    result = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": response_text
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(user_message),
            "completion_tokens": len(response_text),
            "total_tokens": len(user_message) + len(response_text)
        }
    }
```

## 版本说明

### 标准版 (multi_free_api_proxy.py)
- 从`free_api_test`目录自动检测API配置
- 适合动态管理多个API

### V3版 (multi_free_api_proxy_v3.py)
- 从`.env`文件读取API配置 (FREE1_API_KEY, FREE2_API_KEY, FREE3_API_KEY, FREE4_API_KEY, FREE5_API_KEY, FREE6_API_KEY)
- 支持代理配置 (free1使用代理, free2/free3/free4/free5/free6不使用)
- 支持 SDK 调用 (free5 使用 iflow SDK)
- 适合固定配置场景

## 支持的 Free API

### free1 - OpenRouter API
- **Base URL**: https://openrouter.ai
- **Model**: openrouter/free
- **Use Proxy**: 是
- **配置**: FREE1_API_KEY

### free2 - ChatAnywhere API
- **Base URL**: https://api.chatanywhere.tech
- **Model**: gpt-3.5-turbo
- **Use Proxy**: 否
- **配置**: FREE2_API_KEY

### free3 - Free ChatGPT API
- **Base URL**: https://free.v36.cm
- **Model**: gpt-3.5-turbo
- **Use Proxy**: 否
- **配置**: FREE3_API_KEY

### free4 - Mistral AI API
- **Base URL**: https://api.mistral.ai
- **Model**: mistral-small-latest
- **Use Proxy**: 否
- **配置**: FREE4_API_KEY

### free5 - iFlow SDK API
- **Base URL**: iflow (使用 SDK)
- **Model**: iflow
- **Use Proxy**: 否
- **Use SDK**: 是
- **配置**: FREE5_API_KEY (可选)
- **依赖**: iflow-sdk

### free6 - CSDN API
- **Base URL**: https://models.csdn.net
- **Model**: Deepseek-V3
- **Use Proxy**: 否
- **配置**: FREE6_API_KEY

## 许可证

本项目遵循与原项目相同的许可证。
