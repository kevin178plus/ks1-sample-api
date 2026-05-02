# 多Free API代理服务

## 概述

多Free API代理服务是一个能够自动检测、测试和轮换使用多个Free API的代理服务。它会自动检测`free_api_test`目录下的所有Free API(如free2、free3等),并在启动时测试这些API是否可用。如果API可用,则将其加入服务队列,收到请求时轮换使用这些可用的free API。

## 架构设计

本项目采用**模块化架构**，将特殊 API 以独立服务运行，主服务保持轻量级：

### 服务架构
```
┌─────────────────────────────────────────┐
│   主服务 (端口 5000)                     │
│   - 管理普通 API (free1-free4, free6-18)│
│   - 路由特殊 API 到独立服务              │
│   - 统一的 OpenAI API 接口               │
└─────────────┬───────────────────────────┘
              │
              ├──────────────┐
              │              │
         ┌────▼────┐   ┌────▼────┐
         │ free8   │   │  其他   │
         │ (5008)  │   │  API    │
         │ 独立服务│   │  直接调用│
         └─────────┘   └─────────┘
```

### 独立服务
- **free8 (端口 5008)**: Friendli.ai 服务，支持权重模型选择

### 已禁用的API
以下API已停用或过期，配置已在`.env`文件中注释：
- **free5 (iFlow SDK)**: 服务已于2026年3月停用，已从系统中移除
- **free9 (火山方舟Coding Plan)**: Coding Plan已于2026年3月过期

### 新增的API (2026年5月)
以下API已添加到系统中：
- **free15 (Groq)**: llama-3.3-70b-versatile, 需要代理
- **free16 (Sambanova)**: DeepSeek-V3.1, 直连
- **free17 (Cerebras)**: llama3.1-8b, 需要代理
- **free18 (Google Gemini)**: gemini-3-flash-preview, 需要代理

如需重新启用这些API，请在`.env`文件中取消注释对应的API_KEY配置。

### 优势
- ✅ **轻量级**: 主服务不需要安装特殊依赖（如 iflow-sdk）
- ✅ **故障隔离**: 独立服务崩溃不影响主服务
- ✅ **易于维护**: 每个服务职责清晰，代码独立
- ✅ **灵活扩展**: 新增特殊 API 只需添加独立服务

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
10. **独立服务支持**: 特殊 API（如 free5、free8）以独立服务运行
11. **统一接口**: 所有 API 提供统一的 OpenAI 兼容接口
12. **灵活的响应格式处理**: 支持不同 API 返回不同格式的响应
    - 通过 `RESPONSE_FORMAT` 配置定义如何从响应中提取内容
    - 支持多个内容字段优先级
    - 支持合并多个字段的内容
    - 支持 reasoning_content 作为后备字段（适用于 NVIDIA API）
    - 无需修改代理代码，只需在配置文件中定义响应格式
13. **智能 API 切换**: 遇到格式错误时自动切换到下一个 API，无需等待
    - 自动识别 JSON 解析错误等格式问题
    - 格式错误时立即切换，不等待重试延迟
    - 大幅提高系统响应速度和可靠性
14. **失败 API 黑名单**: 临时屏蔽最近失败的 API
    - 返回格式错误的 API 自动加入黑名单（60秒）
    - 选择 API 时自动跳过黑名单中的 API
    - 黑名单记录自动过期和清理
    - 快速恢复健康的 API
15. **详细的诊断日志**: 提供完整的请求/响应诊断信息
    - 记录上游响应状态码、Content-Type、内容长度
    - 记录 JSON 解析错误时的原始响应内容
    - 帮助快速定位上游问题或兼容性问题
16. **自适应权重调整**: 根据 API 表现自动调整权重
    - 成功时权重逐渐降低（避免过度使用）
    - 格式错误时大幅降低权重（-50）
    - 支持手动设置特别权重优先使用

## 安装

### 依赖项

#### 主服务依赖
- Python 3.7+
- Flask
- requests
- watchdog

#### 独立服务依赖（可选）
- iflow-sdk (仅用于 free5 服务)

### 安装依赖

```bash
# 安装主服务依赖
pip install flask requests watchdog

# 如果需要使用 free5，安装 iflow-sdk
pip install iflow-sdk
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

**禁用特定 API 服务**:
如果想禁用某个 API 服务，只需在 `.env` 文件中注释掉或删除对应的 API_KEY 行即可。系统启动时会自动跳过未配置 API_KEY 的服务。

例如，要禁用 free5：
```properties
# FREE5_API_KEY=your_iflow_api_key  # 注释后 free5 将不会被加载
```

**注意**:
- 系统会检查 `.env` 文件中是否配置了对应的 API_KEY 环境变量
- 如果某个 API 的 API_KEY 未配置，即使 `free_api_test/` 目录下有对应的配置文件，该 API 也不会被加载
- 这样可以方便地临时禁用某些 API 服务，而不需要删除或重命名配置文件

### Free API配置

Free API的配置存储在`free_api_test`目录下的各个子目录中,如`free1`、`free2`、`free3`等。每个子目录应包含:

1. `config.py`文件,其中包含API的配置信息
2. `test_api.py`文件,用于测试API是否可用
3. README文件(README.md、readme.txt或README.txt),其中包含支持的模型列表

#### config.py 配置格式

每个API的`config.py`文件应包含以下配置:

```python
# API配置
import os

API_KEY = os.getenv("FREE*_API_KEY")
BASE_URL = "https://api.example.com"
MODEL_NAME = "model-name"
USE_PROXY = False  # 是否使用代理
USE_SDK = False  # 是否使用SDK
```

**配置说明**:
- `API_KEY`: 从环境变量读取API密钥
- `BASE_URL`: API的基础URL(不包含`/v1/`路径)
- `MODEL_NAME`: 使用的模型名称
- `USE_PROXY`: 是否使用HTTP代理(默认False)
- `USE_SDK`: 是否使用SDK调用(默认False)

**特殊处理**:
- `free1`: 强制使用代理(`USE_PROXY = True`)
- `free5`: 独立服务运行，主服务通过 HTTP 调用（端口 5005）
- `free8`: 独立服务运行，支持权重模型选择（端口 5008）

#### 自动发现机制

服务启动时会自动:
1. 扫描`free_api_test`目录下的所有`free*`子目录
2. 读取每个子目录的`config.py`文件
3. **检查 `.env` 文件中是否配置了对应的 API_KEY 环境变量**
4. 如果 API_KEY 已配置，则提取配置信息并构建API配置字典
5. 如果 API_KEY 未配置，则跳过该 API（并在日志中显示跳过原因）
6. 测试每个已配置的API是否可用
7. 将可用的API加入服务队列

**优势**:
- 无需修改代码即可添加新API
- 配置集中管理,易于维护
- 支持动态加载和卸载API
- 配置格式统一,易于理解
- **可以通过注释 `.env` 中的 API_KEY 来方便地禁用特定服务**

#### test_api.py 文件

每个API的`test_api.py`文件用于测试API是否可用:

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

#### 一键启动所有服务（推荐）

Windows:
```bash
start_all_services.bat  # 启动主服务 + 所有独立服务
```

此脚本会自动：
1. 检查并安装依赖
2. 启动 free5 独立服务（端口 5005）
3. 启动 free8 独立服务（端口 5008）
4. 启动主服务（端口 5000）

#### 分步启动

如果需要单独控制各个服务：

**Windows**:
```bash
start_multi_free_api.bat        # 标准版本
start_multi_free_api_v3.bat     # V3版本(从.env读取配置)
```

**Linux/Mac**:
```bash
python multi_free_api_proxy.py       # 标准版本
python multi_free_api_proxy_v3.py    # V3版本
```

#### 单独启动独立服务

**free5 服务** (需要 iflow-sdk):
```bash
cd free_api_test/free5
python iflow_api_proxy.py
```

**free8 服务**:
```bash
cd free_api_test/free8
python friendli_service.py
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

#### 独立服务端点

**free5 服务** (端口 5005):
```bash
# 健康检查
curl http://localhost:5005/health

# 列出模型
curl http://localhost:5005/v1/models

# 聊天完成
curl -X POST http://localhost:5005/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

**free8 服务** (端口 5008):
```bash
# 健康检查
curl http://localhost:5008/health

# 列出模型
curl http://localhost:5008/v1/models

# 统计信息
curl http://localhost:5008/v1/stats

# 聊天完成
curl -X POST http://localhost:5008/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

## 调试模式

### 启用调试模式

在 `multi_free_api_proxy` 目录下创建一个名为 `DEBUG_MODE.txt` 的空文件：

```bash
cd multi_free_api_proxy
type nul > DEBUG_MODE.txt
```

> **注意**：调试模式文件必须放在 `multi_free_api_proxy/` 目录下（即主服务的运行目录），不是项目根目录。如果放在根目录，主服务无法检测到调试模式。

### 调试面板

启用调试模式后，访问 `http://localhost:5000/debug` 可以查看Web调试面板，包含:

- **统计信息**: 总调用次数、成功/失败/超时/重试计数
- **API状态**: 所有Free API的可用状态、成功/失败次数、最近测试时间和结果，支持单个或全部重新测试
- **测试聊天**: 直接在页面上测试API功能

#### 统计信息说明

统计信息记录在`CACHE_DIR`目录下的`CALLS_{日期}.json`文件中，包含:

- `date`: 统计日期(YYYYMMDD格式)
- `total`: 总调用次数(成功+失败+超时)
- `success`: 成功次数
- `failed`: 失败次数
- `timeout`: 超时次数
- `retry`: 重试次数
- `last_updated`: 最后更新时间

**计数规则**:
- 每次请求成功时，`success`和`total`各+1
- 每次请求失败时，`failed`和`total`各+1
- 每次请求超时时，`timeout`和`total`各+1
- 每次重试时，`retry`+1(不影响total)

**统计示例**:
```json
{
  "date": "20260220",
  "total": 10,
  "success": 7,
  "failed": 2,
  "timeout": 1,
  "retry": 3,
  "last_updated": "2026-02-20T22:30:00.123456"
}
```

### 调试API端点

#### 调试统计

**端点**: `GET /debug/stats`

**请求示例**:
```bash
curl http://localhost:5000/debug/stats
```

#### 调试日志

启用调试模式后，所有请求和响应都会被记录到`CACHE_DIR`目录，文件名格式为:

```
{时间戳}_{类型}_{消息ID}.json
```

**日志文件包含**:
- `timestamp`: 请求时间
- `type`: 消息类型(REQUEST/RESPONSE/ERROR)
- `message_id`: 消息ID
- `api_name`: 使用的API名称(如free1、free2等)
- `data`: 请求数据或响应数据

**示例日志文件**:
```json
{
  "timestamp": "2026-02-20T22:33:06.607",
  "type": "REQUEST",
  "message_id": "7001c957",
  "api_name": "free2",
  "data": {
    "model": "gpt-3.5-turbo",
    "messages": [...]
  }
}
```

**响应日志示例**:
```json
{
  "timestamp": "2026-02-20T22:33:07.123",
  "type": "RESPONSE",
  "message_id": "7001c957",
  "api_name": "free2",
  "data": {
    "id": "chatcmpl-abc123",
    "model": "gpt-3.5-turbo",
    "choices": [...],
    "_retry_count": 0,
    "_api_name": "free2"
  }
}
```

**错误日志示例**:
```json
{
  "timestamp": "2026-02-20T22:33:08.456",
  "type": "ERROR",
  "message_id": "abc12345",
  "api_name": "unknown",
  "data": {
    "error": "Free API error: Connection timeout",
    "error_type": "timeout",
    "_api_name": "unknown"
  }
}
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
5. **智能 API 切换**: 如果遇到格式错误（如 JSON 解析失败），系统会自动切换到下一个 API
   - 查看日志中的 `[黑名单]` 和 `[重试] 消息
   - 格式错误的 API 会被临时加入黑名单（60秒）
   - 权重会大幅降低（-50），减少再次被选中的概率
6. **诊断上游问题**: 查看日志中的 `[诊断]` 消息
   - 检查上游响应状态码
   - 检查 Content-Type 是否为 `application/json`
   - 查看原始响应内容（如果有 JSON 解析错误）
   - 参考 `DEBUG_GUIDE.md` 获取详细的诊断步骤

## 扩展

### 添加新 API

要添加新的 Free API,只需在`free_api_test`目录下创建一个新的子目录,并在其中创建配置文件。服务会在下次启动时自动检测并测试新的API。

#### 步骤

1. **创建API目录**: 在`free_api_test`目录下创建新目录(如`free19`)
2. **创建config.py**: 在新目录中创建`config.py`文件
3. **配置环境变量**: 在`.env`文件中添加API密钥
4. **重启服务**: 重启服务以加载新API

#### config.py 示例

```python
# API配置
import os

API_KEY = os.getenv("FREE19_API_KEY")
BASE_URL = "https://api.example.com"
MODEL_NAME = "gpt-3.5-turbo"
USE_PROXY = False  # 是否使用代理
USE_SDK = False  # 是否使用SDK
MAX_TOKENS = 2000
DEFAULT_WEIGHT = 10

# 响应格式配置（可选）
RESPONSE_FORMAT = {
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
```

#### RESPONSE_FORMAT 配置说明

不同 API 可能返回不同格式的响应，`RESPONSE_FORMAT` 配置用于定义如何从响应中提取内容。

**配置项说明**:

- **content_fields**: 内容字段优先级列表（按优先级从高到低）
  - 标准格式: `["content"]`
  - NVIDIA API: `["content", "reasoning_content"]`

- **merge_fields**: 是否需要合并多个字段的内容
  - `False`: 按优先级提取第一个非空字段（默认）
  - `True`: 合并所有非空字段的内容

- **field_separator**: 字段分隔符（如果需要合并）
  - 默认: `"\n\n---\n\n"`

- **use_reasoning_as_fallback**: 是否在 content 为空时使用 reasoning_content
  - `False`: 不使用（默认）
  - `True`: 当所有 content_fields 都为空时，使用 reasoning_content 作为后备

**不同 API 的配置示例**:

**标准 API** (如 free1, free2):
```python
RESPONSE_FORMAT = {
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
```

**NVIDIA API** (如 free7):
```python
RESPONSE_FORMAT = {
    "content_fields": ["content", "reasoning_content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": True
}
```

#### .env 配置

```properties
# 新API的密钥
FREE19_API_KEY=your_api_key_here
```

#### 特殊API配置

**使用代理的API** (如free1, free15, free17, free18):
```python
API_KEY = os.getenv("FREE1_API_KEY")
BASE_URL = "https://openrouter.ai"
MODEL_NAME = "openrouter/free"
USE_PROXY = True  # 使用代理
USE_SDK = False
```

**使用SDK的API** (如free5, free17, free18):
```python
API_KEY = os.getenv("FREE5_API_KEY", "iflow-sdk")  # SDK可能不需要密钥
BASE_URL = "iflow"
MODEL_NAME = "iflow"
USE_PROXY = False
USE_SDK = True  # 使用SDK
```

**NVIDIA API** (如free7):
```python
API_KEY = os.getenv("FREE7_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/"
MODEL_NAME = "z-ai/glm4.7"
USE_PROXY = False  # 不使用代理
USE_SDK = False  # 使用HTTP API

# 响应格式配置
RESPONSE_FORMAT = {
    "content_fields": ["content", "reasoning_content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": True
}
```

**说明**: 
- NVIDIA API 可能返回 `content` 为 `null` 的情况
- 实际内容在 `reasoning_content` 字段中（这是模型的思考过程）
- 配置 `content_fields` 为 `["content", "reasoning_content"]` 表示优先使用 content，如果为空则使用 reasoning_content
- 配置 `use_reasoning_as_fallback: True` 表示当所有字段都为空时，使用 reasoning_content 作为后备
- **注意**: `reasoning_content` 是思考过程，不是最终答案。如果需要最终答案，应该确保 `content` 字段有值（可能需要调整 max_tokens 参数）

### 添加 SDK API

### 添加普通 HTTP API

1. 在`free_api_test`目录下创建新的子目录（如 `free19`）
2. 创建 `config.py` 文件，配置 API 信息
3. 创建 `test_api.py` 文件，用于测试 API
4. 在 `.env` 文件中添加对应的 API_KEY
5. 重启服务，系统会自动加载新 API

### 添加独立服务（特殊 API）

如果新 API 有特殊需求（如需要特殊 SDK、权重模型选择等），建议创建独立服务：

1. 在 `free_api_test/freeN/` 目录下创建独立服务文件
2. 提供标准的 OpenAI API 兼容接口（`/v1/chat/completions`, `/v1/models`, `/health`）
3. 使用独立端口（建议 5000 + N）
4. 在主服务的 `execute_with_free_api` 函数中添加路由逻辑
5. 在 `test_api_startup` 函数中添加独立服务测试逻辑
6. 更新启动脚本 `start_all_services.bat`

**优势**：
- 不影响主服务的轻量级特性
- 故障隔离，不影响其他服务
- 可以独立测试和调试
- 便于维护和升级
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
- 从`free_api_test`目录自动加载API配置
- 使用统一的`config.py`配置文件格式
- 自动发现和加载所有`free*`子目录
- 支持代理配置 (free1使用代理, free2/free3/free4/free5/free6不使用)
- 支持 SDK 调用 (free5 使用 iflow SDK)
- 完整的统计信息记录 (成功/失败/超时/重试)
- 调试日志中记录使用的API名称
- 适合动态扩展和管理多个API

**V3 版本主要特性**:
1. **自动发现**: 无需修改代码即可添加新API
2. **统一配置**: 所有API使用相同的配置格式
3. **完整统计**: 记录所有请求的成功/失败/超时/重试次数
4. **调试增强**: 日志中显示使用的API名称
5. **易于扩展**: 添加新API只需创建目录和配置文件

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

### free7 - NVIDIA API
- **Base URL**: https://integrate.api.nvidia.com/
- **Model**: z-ai/glm4.7
- **Use Proxy**: 否
- **Use SDK**: 否
- **配置**: FREE7_API_KEY
- **特殊说明**: 
  - NVIDIA API 可能返回 `content` 为 `null` 的情况
  - 实际内容在 `reasoning_content` 字段中（这是模型的思考过程）
  - 已配置 RESPONSE_FORMAT 来正确处理这种情况
  - 建议根据问题复杂度调整 max_tokens 参数（简单问题 1024-2048，复杂问题 4096-8192）

### free8 - Friendli.ai API
- **Base URL**: https://api.friendli.ai/serverless/v1
- **Model**: meta-llama/Llama-3.3-70B-Instruct
- **Use Proxy**: 否
- **Use SDK**: 否
- **配置**: FREE8_API_KEY
- **状态**: 独立服务 (端口 5008)

### free10 - API 10
- **Base URL**: Unknown
- **Model**: Various
- **Use Proxy**: 否
- **配置**: FREE10_API_KEY

### free11 - API 11
- **Base URL**: Unknown
- **Model**: Various
- **Use Proxy**: 否
- **配置**: FREE11_API_KEY

### free12 - API 12
- **Base URL**: Unknown
- **Model**: Various
- **Use Proxy**: 否
- **配置**: FREE12_API_KEY

### free13 - Volcengine API
- **Base URL**: https://ark.cn-beijing.volces.com/api/coding
- **Model**: ark-code-latest
- **Use Proxy**: 否
- **配置**: FREE13_API_KEY

### free14 - CogView API
- **Base URL**: https://cogview.api
- **Model**: cgc-apikey
- **Use Proxy**: 否
- **配置**: FREE14_API_KEY

### free15 - Groq API ⚡
- **Base URL**: https://api.groq.com/openai/v1
- **Model**: llama-3.3-70b-versatile
- **Use Proxy**: 是 (127.0.0.1:7897)
- **Use SDK**: 否
- **配置**: GROQ_API_KEY
- **特殊说明**: 
  - 超快的 LLM 推理服务
  - 需要通过 HTTP 代理访问
  - 支持多种 Llama 模型

### free16 - Sambanova API ⚡
- **Base URL**: https://api.sambanova.ai/v1
- **Model**: DeepSeek-V3.1
- **Use Proxy**: 否
- **Use SDK**: 否
- **配置**: SAMBANOVA_API_KEY
- **特殊说明**: 
  - 高性能 LLM 服务
  - 支持 DeepSeek 和 Llama 系列模型

### free17 - Cerebras API ⚡
- **Base URL**: https://api.cerebras.ai/v1
- **Model**: llama3.1-8b
- **Use Proxy**: 是 (127.0.0.1:7897)
- **Use SDK**: 是
- **配置**: CEREBRAS_API_KEY
- **依赖**: cerebras-cloud-sdk
- **特殊说明**: 
  - 基于 Cerebras Wafer-Scale Engine 的快速推理
  - 需要通过 HTTP 代理访问
  - 支持 Llama 和 GPT 系列模型

### free18 - Google Gemini API ⚡
- **Base URL**: https://generativelanguage.googleapis.com/v1beta
- **Model**: gemini-3-flash-preview
- **Use Proxy**: 是 (127.0.0.1:7897)
- **Use SDK**: 是
- **配置**: GEMINI_API_KEY
- **依赖**: google-genai
- **特殊说明**: 
  - Google 先进的多模态 AI 模型
  - 需要通过 HTTP 代理访问
  - 支持多种 Gemini 模型

## 常见问题

### Q: 为什么有些 API 以独立服务运行？

A: 为了保持主服务的轻量级和稳定性。特殊 API（如 free5 需要 iflow-sdk、free8 需要权重模型选择）以独立服务运行，有以下优势：
- 主服务不需要安装特殊依赖
- 独立服务崩溃不影响主服务
- 可以独立测试和调试
- 便于维护和升级

### Q: 如何只启动主服务，不启动独立服务？

A: 直接运行主服务即可：
```bash
cd multi_free_api_proxy
python multi_free_api_proxy_v3.py
```
注意：如果未启动独立服务，主服务会自动跳过 free5 和 free8。

### Q: 独立服务启动失败怎么办？

A: 检查以下几点：
1. 端口是否被占用（5005 和 5008）
2. 依赖是否安装（free5 需要 iflow-sdk）
3. `.env` 文件中是否配置了对应的 API_KEY
4. 查看独立服务的错误日志

### Q: 如何禁用某个独立服务？

A: 在 `.env` 文件中注释掉对应的 API_KEY：
```properties
# FREE5_API_KEY=your_iflow_api_key  # 注释后 free5 将不会被加载
# FREE8_API_KEY=your_friendli_token  # 注释后 free8 将不会被加载
```

### Q: 主服务和独立服务如何通信？

A: 主服务通过 HTTP 调用独立服务的标准 OpenAI API 接口：
- free5: http://localhost:5005/v1/chat/completions
- free8: http://localhost:5008/v1/chat/completions

### Q: 可以修改独立服务的端口吗？

A: 可以。修改对应服务文件中的 `PORT` 变量，并更新主服务中的路由逻辑。

## 许可证

本项目遵循与原项目相同的许可证。
