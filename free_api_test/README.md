# Free API Test

This directory contains tests and examples for multiple Free AI API services.

## Overview

This test suite provides access to multiple free AI API services through a unified interface. Each free API service is located in its own subdirectory (free1-free21) and provides access to different AI models.

## Available Services

### free1 - OpenRouter API
- **Provider**: OpenRouter
- **Base URL**: https://openrouter.ai
- **Models**: openrouter/free, gpt-3.5-turbo, gpt-4, claude-3-opus, gemini-pro
- **Features**: Multiple model providers in one API
- **Status**: ✅ Active
- **Proxy**: Required
- **Documentation**: See [free1/README.md](free1/README.md)

### free2 - ChatAnywhere API
- **Provider**: ChatAnywhere
- **Base URL**: https://api.chatanywhere.tech
- **Models**: gpt-3.5-turbo, gpt-4o-mini, deepseek-v3
- **Features**: Free access to OpenAI-compatible API
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free2/readme.txt](free2/readme.txt)

### free3 - Free ChatGPT API
- **Provider**: Free.v36.cm
- **Base URL**: https://free.v36.cm
- **Models**: gpt-4o-mini, gpt-3.5-turbo-0125, gpt-3.5-turbo-1106, gpt-3.5-turbo, gpt-3.5-turbo-16k
- **Features**: Free access with 200 requests/day limit
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free3/README.md](free3/README.md)

### free4 - Mistral AI API
- **Provider**: Mistral AI
- **Base URL**: https://api.mistral.ai
- **Models**: mistral-small-latest, mistral-medium-latest, mistral-large-latest, open-mistral-nemo
- **Features**: High-performance European AI models
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free4/README.md](free4/README.md)

### free6 - CSDN API
- **Provider**: CSDN
- **Base URL**: https://models.csdn.net
- **Models**: Deepseek-V3
- **Features**: Deepseek model access
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free6/config.py](free6/config.py)

### free7 - NVIDIA API
- **Provider**: NVIDIA
- **Base URL**: https://integrate.api.nvidia.io
- **Models**: Various NVIDIA hosted models
- **Features**: High-performance GPU-accelerated inference
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free7/README.md](free7/README.md)

### free8 - Friendli.ai API
- **Provider**: Friendli.ai
- **Base URL**: https://api.friendli.ai/serverless/v1
- **Models**: meta-llama/Llama-3.3-70B-Instruct, Qwen/Qwen3-235B-A22B-Instruct-2507, MiniMaxAI/MiniMax-M2.5, zai-org/GLM-4.7, zai-org/GLM-5
- **Features**: High-performance LLM service with OpenAI SDK compatibility
- **Status**: ✅ Active (独立服务)
- **Proxy**: No
- **Documentation**: See [free8/README.md](free8/README.md)

### free9 - 火山方舟 Coding Plan API ⚠️ **已过期**
- **Provider**: 火山方舟 (Volcengine)
- **Base URL**: https://ark.cn-beijing.volces.com/api/coding
- **Models**: ark-code-latest
- **Features**: Coding Plan API compatible with OpenAI standard
- **Status**: ❌ Coding Plan expired in March 2026
- **Documentation**: See [free9/README.md](free9/README.md)

### free10 - API 10
- **Provider**: Unknown
- **Status**: ✅ Active
- **Proxy**: No

### free11 - API 11
- **Provider**: Unknown
- **Status**: ✅ Active
- **Proxy**: No

### free12 - API 12
- **Provider**: Unknown
- **Status**: ✅ Active
- **Proxy**: No

### free13 - Volcengine API
- **Provider**: Volcengine
- **Base URL**: https://ark.cn-beijing.volces.com/api/coding
- **Models**: ark-code-latest
- **Features**: Coding Plan API compatible with OpenAI standard
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free13/README.md](free13/README.md)

### free14 - CogView API
- **Provider**: CogView
- **Base URL**: https://cogview.api
- **Models**: cgc-apikey
- **Features**: CogView API access
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free14/config.py](free14/config.py)

### free15 - Groq API ⚡
- **Provider**: Groq
- **Base URL**: https://api.groq.com/openai/v1
- **Models**: llama-3.3-70b-versatile, llama-3.1-8b-instant, qwen/qwen3-32b
- **Features**: Ultra-fast LLM inference
- **Status**: ✅ Active
- **Proxy**: **Required** (127.0.0.1:7897)
- **Documentation**: See [free15/README.md](free15/README.md)

### free16 - Sambanova API ⚡
- **Provider**: Sambanova
- **Base URL**: https://api.sambanova.ai/v1
- **Models**: DeepSeek-V3.1, DeepSeek-V3.2, Llama-4-Maverick-17B
- **Features**: High-performance LLM service
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free16/README.md](free16/README.md)

### free17 - Cerebras API ⚡
- **Provider**: Cerebras
- **Base URL**: https://api.cerebras.ai/v1
- **Models**: llama3.1-8b, llama3.1-70b, gpt-oss-120b
- **Features**: Fast inference with Cerebras Wafer-Scale Engine
- **Status**: ✅ Active
- **Proxy**: **Required** (127.0.0.1:7897)
- **Documentation**: See [free17/README.md](free17/README.md)

### free18 - Google Gemini API ⚡
- **Provider**: Google
- **Base URL**: https://generativelanguage.googleapis.com/v1beta
- **Models**: gemini-3-flash-preview, gemini-2.0-flash-exp, gemini-1.5-flash
- **Features**: Advanced multimodal AI models
- **Status**: ✅ Active
- **Proxy**: **Required** (127.0.0.1:7897)
- **Documentation**: See [free18/README.md](free18/README.md)

### free19 - API 19
- **Provider**: Unknown
- **Status**: ✅ Active
- **Proxy**: No

### free20 - LongCat API
- **Provider**: LongCat
- **Base URL**: https://api.longcat.xyz
- **Features**: OpenAI-compatible API
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free20/config.py](free20/config.py)

### free21 - FreeModel API
- **Provider**: FreeModel
- **Base URL**: https://api.freemodel.dev
- **Features**: OpenAI-compatible API
- **Status**: ✅ Active
- **Proxy**: No
- **Documentation**: See [free21/config.py](free21/config.py)

## Requirements

- Python 3.7+
- requests library
- google-genai (for free18)
- cerebras-cloud-sdk (for free17)
- Valid API keys for respective services

## Installation

1. Install required dependencies:
```bash
pip install requests
# Optional: install SDKs for specific APIs
pip install google-genai  # for free18 (Gemini)
pip install cerebras-cloud-sdk  # for free17 (Cerebras)
```

2. Configure API keys in the `.env` file:
```properties
FREE1_API_KEY=your_openrouter_api_key
FREE3_API_KEY=your_free_v36_api_key
FREE4_API_KEY=your_mistral_api_key
FREE6_API_KEY=your_csdn_api_key
FREE7_API_KEY=your_nvidia_api_key
FREE8_API_KEY=your_friendli_api_key
FREE10_API_KEY=your_api10_key
FREE11_API_KEY=your_api11_key
FREE12_API_KEY=your_api12_key
FREE13_API_KEY=your_volcengine_api_key
FREE14_API_KEY=your_cogview_api_key
FREE15_API_KEY=your_groq_api_key
FREE16_API_KEY=your_sambanova_api_key
FREE17_API_KEY=your_cerebras_api_key
FREE18_API_KEY=your_gemini_api_key
FREE19_API_KEY=your_api19_key
LONGCAT_API_KEY=your_longcat_api_key
FREEMODEL_API_KEY=your_freemodel_api_key
```

**Disabling Specific Services**:
To disable a specific API service, simply comment out or delete the corresponding API_KEY line in the `.env` file. The system will automatically skip services without configured API keys.

Currently disabled services:
- free9 (火山方舟 Coding Plan): Coding Plan expired in March 2026

For example, to disable a service:
```properties
# FREE9_API_KEY=your_api9_key  # Commented out - free9 will not be loaded
```

**Note**:
- The system checks if the corresponding API_KEY environment variable is configured in `.env`
- If an API's API_KEY is not configured, even if the configuration file exists in `free_api_test/` directory, that API will not be loaded
- This allows you to easily temporarily disable certain API services without deleting or renaming configuration files

## Usage

### Running Individual Tests

Each free API has its own test script:
```bash
cd free1
python test_api.py

cd ../free15
python test_api.py

cd ../free16
python test_api.py

cd ../free17
python test_api.py

cd ../free18
python test_api.py
```

### Using Multi API Proxy

See [../multi_free_api_proxy/MULTI_FREE_API_README.md](../multi_free_api_proxy/MULTI_FREE_API_README.md) for information about using the unified proxy service that automatically manages and rotates between multiple free APIs.

## Notes

- Each free API has its own rate limits and usage quotas
- Monitor your usage through each provider's dashboard
- For production use, consider upgrading to paid plans
- Some APIs may require proxy configuration (see individual documentation)

## Multi API Proxy Integration

All free APIs (free1-free21) can be used through the multi_free_api_proxy service, which:
- Automatically detects and tests all available APIs
- Rotates between APIs for load balancing
- Handles API failures and retries
- Provides unified OpenAI-compatible interface
- **Routes special API (free8) to independent service**

### Architecture

```
主服务 (端口 5000)
  ├── free1-free4, free6-free7, free9-free21: 直接调用
  └── free8: 路由到独立服务 (端口 5008)
```

### Starting All Services

To start all services (main + independent):
```bash
035-start_all_services.bat  # Windows
```

For more details, see the [multi_free_api_proxy documentation](../multi_free_api_proxy/).

## 🔌 添加新的免费 API

1. 在 `free_api_test/` 目录下创建新目录 `free{N}`
2. 创建 `config.py` 文件，参考现有配置：
```python
import os

TITLE_NAME = "API Name"
API_KEY = os.getenv("FREE{N}_API_KEY")
BASE_URL = "https://api.provider.com"
MODEL_NAME = "model-id"
USE_PROXY = False  # 或 True 如果需要代理
USE_SDK = False    # 或 True 如果使用 SDK
MAX_TOKENS = 2000
DEFAULT_WEIGHT = 10
RESPONSE_FORMAT = {
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
```
3. 创建 `README.md` 文档
4. 创建 `test_api.py` 测试脚本
5. 在 `.env` 文件中添加 API Key
6. 重启服务

详见：[free15/README.md](free15/README.md), [free16/README.md](free16/README.md), [free17/README.md](free17/README.md), [free18/README.md](free18/README.md)

## 📊 API 状态概览

| API | Provider | Model | Proxy | Status |
|-----|----------|-------|-------|--------|
| free1 | OpenRouter | openrouter/free | Yes | ✅ |
| free2 | ChatAnywhere | gpt-3.5-turbo | No | ✅ |
| free3 | Free.v36.cm | gpt-4o-mini | No | ✅ |
| free4 | Mistral AI | mistral-small | No | ✅ |
| free6 | CSDN | DeepSeek-V3 | No | ✅ |
| free7 | NVIDIA | nvidia/llama | No | ✅ |
| free8 | Friendli.ai | llama-3.3-70B | - | ✅* |
| free9 | Volcengine | ark-code-latest | - | ❌ |
| free10-12 | Unknown | various | No | ✅ |
| free13 | Volcengine | ark-code-latest | No | ✅ |
| free14 | CogView | cgc-apikey | No | ✅ |
| free15 | Groq | llama-3.3-70b | Yes | ✅ |
| free16 | Sambanova | DeepSeek-V3.1 | No | ✅ |
| free17 | Cerebras | llama3.1-8b | Yes | ✅ |
| free18 | Google Gemini | gemini-3-flash | Yes | ✅ |
| free19 | Unknown | various | No | ✅ |
| free20 | LongCat | openrouter/free | No | ✅ |
| free21 | FreeModel | freemodel | No | ✅ |

**Legend:**
- ✅ Active - Service is available
- ❌ Disabled - Service is disabled or expired
- * - Independent service (runs on separate port)
- Yes - Requires HTTP proxy (127.0.0.1:7897)
