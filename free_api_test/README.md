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
- **Status**: ✅ Active — 🔧 2026-05-27 反转 use_proxy 后恢复（原配置超时）
- **Proxy**: **Required** (127.0.0.1:7897)
- **Documentation**: See [free4/README.md](free4/README.md)

### free6 - CSDN API ⛔
- **Provider**: CSDN
- **Base URL**: https://models.csdn.net
- **Models**: Deepseek-V3
- **Features**: Deepseek model access
- **Status**: ⛔ 失效 — HTTP 400，接口格式可能已变更
- **Proxy**: No
- **Documentation**: See [free6/config.py](free6/config.py)

### free7 - NVIDIA API ⛔
- **Provider**: NVIDIA
- **Base URL**: https://integrate.api.nvidia.com
- **Models**: minimax-m2.5
- **Features**: High-performance GPU-accelerated inference
- **Status**: ⛔ 失效 — HTTP 410 Gone，接口已下线
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

### free10 - 联通云 API ⛔
- **Provider**: 联通云 (CUCC)
- **Base URL**: https://aigw-gzgy2.cucloud.cn:8443
- **Models**: unicom-cloud/Minimax-M2.5
- **Status**: ⛔ 失效 — HTTP 403，需认证或已限流
- **Proxy**: No

### free11 - 白山智算 API ⛔
- **Provider**: 白山智算 (EdgeFn)
- **Base URL**: https://api.edgefn.net
- **Models**: DeepSeek-R1-0528-Qwen3-8B
- **Status**: ⛔ 失效 — HTTP 403，需认证
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

### free14 - CGC ChanCloud AI API ⛔
- **Provider**: CGC ChanCloud
- **Base URL**: https://cgc.chancloud.com/cgc/api/public/ai/server
- **Models**: Nemotron-3-Super-120B-A12B
- **Features**: CogView/ChanCloud AI access
- **Status**: ⛔ 失效 — DNS/连接失败，服务可能已关闭
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

### free18 - Google Gemini API ⚠️
- **Provider**: Google
- **Base URL**: https://generativelanguage.googleapis.com/v1beta
- **Models**: gemini-3-flash-preview, gemini-2.0-flash-exp, gemini-1.5-flash
- **Features**: Advanced multimodal AI models
- **Status**: ⚠️ 超时 — 连接超时，反转代理后仍失败，需排查网络
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
- free5 (iFlow SDK)：2026年3月正式关停
- free7 (NVIDIA)：2026年5月返回 HTTP 410 Gone，接口已下线
- free9 (火山方舟 Coding Plan)：Coding Plan 2026年3月过期

⚠️ 以下服务当前连接失败，建议暂时禁用或排查：
- free6 (CSDN)：HTTP 400
- free10 (联通云)：HTTP 403
- free11 (白山智算)：HTTP 403
- free14 (CGC ChanCloud)：DNS/连接失败
- free18 (Google Gemini)：连接超时

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
- **Use `test_upstreams_proxy_swap.py` in project root to automatically test all upstreams and try reversing `use_proxy` for failed ones**

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

> **📅 最后检测时间：2026-05-27** — 使用 `test_upstreams_proxy_swap.py` 自动测试

| API | Provider | Model | Proxy | Status | 备注 |
|-----|----------|-------|-------|--------|------|
| free1 | OpenRouter | openrouter/free | Yes | ✅ | |
| free2 | ChatAnywhere | gpt-3.5-turbo | No | ✅ | |
| free3 | Free.v36.cm | gpt-4o-mini | No | ✅ | |
| free4 | Mistral AI | mistral-small | **Yes** | ✅ | 🔧 反转 use_proxy 后恢复 |
| free5 | iFlow SDK | various | - | ❌ 已关停 | |
| free6 | CSDN | DeepSeek-V3 | No | ⛔ 失效 | HTTP 400 |
| free7 | NVIDIA | minimax-m2.5 | No | ⛔ 失效 | HTTP 410 Gone |
| free8 | Friendli.ai | Qwen3-235B | - | ✅* | 独立服务 |
| free9 | Volcengine | ark-code-latest | - | ❌ | Coding Plan 2026年3月过期 |
| free10 | 联通云 | Minimax-M2.5 | No | ⛔ 失效 | HTTP 403 |
| free11 | 白山智算 | DeepSeek-R1 | No | ⛔ 失效 | HTTP 403 |
| free12 | OpenCode AI | minimax-m2.5-free | No | ✅ | |
| free13 | atomgit | Qwen3.5 | No | ✅ | |
| free14 | CGC ChanCloud | Nemotron-3 | No | ⛔ 失效 | DNS/连接失败 |
| free15 | Groq | llama-3.3-70b | Yes | ✅ | |
| free16 | Sambanova | DeepSeek-V3.1 | No | ✅ | |
| free17 | Cerebras | llama3.1-8b | Yes | ✅ | |
| free18 | Google Gemini | gemini-3-flash | Yes | ⚠️ 超时 | 反转代理后仍超时 |
| free19 | Cohere | command-a | Yes | ✅ | |
| free20 | LongCat | LongCat-Flash | No | ✅ | |
| free21 | FreeModel | freemodel-default | Yes | ✅ | |
| free22 | 商汤日日新 | sensenova-6.7 | No | ✅ | |

**Legend:**
- ✅ Active - Service is available
- ⛔ 失效 - Connection failed (HTTP error/DNS failure)

---

## 📊 Infographics

Project infographics generated with SenseNova U1 Fast (2K resolution 2752×1536):

| # | Topic | File |
|---|-------|------|
| **01** | Project Overview — 3 core metrics + hub architecture | [ks1-simple-api-01-全景图-v2.png](../ks1-simple-api-01-全景图-v2.png) |
| **02** | Dual Engine — Python Flask vs Go comparison | [ks1-simple-api-02-双引擎架构-v2.png](../ks1-simple-api-02-双引擎架构-v2.png) |
| **03** | Upstream Status Map — 22 upstreams status grid | [ks1-simple-api-03-上游状态全景-v2.png](../ks1-simple-api-03-上游状态全景-v2.png) |
| **04** | Deployment Scenarios & Workflow — 4 scenarios + 5-step flow | [ks1-simple-api-04-部署场景与工作流-v2.png](../ks1-simple-api-04-部署场景与工作流-v2.png) |

> 💡 v1 versions (Chinese text) had garbled text issues from AI rendering. v2 versions (English-dominant) are the recommended replacements. Generation scripts: `generate_infographic_01_v2.py` ~ `generate_infographic_04_v2.py` in project root.
- ⚠️ 超时 - Connection timeout, needs investigation
- ❌ Disabled - Service is disabled or expired
- * - Independent service (runs on separate port)
- Yes - Requires HTTP proxy (127.0.0.1:7897)
- 🔧 - Fixed by reversing `use_proxy` parameter during this test
