# 多Free API代理服务

## 概述

多Free API代理服务是一个能够自动检测、测试和轮换使用多个Free API的代理服务。它会自动检测`free_api_test`目录下的所有Free API(如free2、free3等),并在启动时测试这些API是否可用。如果API可用,则将其加入服务队列,收到请求时轮换使用这些可用的free API。

## 功能特性

1. **自动检测**: 自动检测`free_api_test`目录下的所有Free API
2. **自动测试**: 启动时测试所有Free API是否可用
3. **轮换使用**: 收到请求时轮换使用可用的Free API
4. **定期测试**: 定期(默认5分钟)重新测试所有Free API的可用性
5. **错误重试**: 支持请求失败时自动重试
6. **并发控制**: 支持并发请求控制
7. **调试模式**: 支持调试模式,记录请求和响应
8. **健康检查**: 提供健康检查端点
9. **自动模型选择**: 忽略原始请求中的model参数,自动使用每个API支持的第一个模型

## 安装

### 依赖项

- Python 3.7+
- Flask
- requests
- watchdog

### 安装依赖

```bash
pip install flask requests watchdog
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
start_multi_free_api.bat
```

Linux/Mac:
```bash
python multi_free_api_proxy.py
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

## 调试模式

要启用调试模式,在项目根目录创建一个名为`DEBUG_MODE.txt`的空文件:

```bash
touch DEBUG_MODE.txt
```

启用调试模式后,所有请求和响应将被保存到缓存目录中。

## 工作原理

1. **启动阶段**:
   - 检测`free_api_test`目录下的所有Free API
   - 测试每个Free API是否可用
   - 将可用的API加入服务队列

2. **请求处理**:
   - 从服务队列中获取下一个可用的API
   - 使用该API处理请求
   - 将该API移到队列末尾,实现轮换

3. **定期测试**:
   - 每隔5分钟重新测试所有Free API
   - 更新服务队列

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

### 请求失败

1. 检查请求格式是否正确
2. 检查是否有可用的API
3. 查看日志了解详细错误信息

## 扩展

要添加新的Free API,只需在`free_api_test`目录下创建一个新的子目录,并在其中创建一个`test_api.py`文件,包含API的配置信息。服务会在下次启动时自动检测并测试新的API。

## 许可证

本项目遵循与原项目相同的许可证。
