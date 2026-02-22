# Free API Test

This directory contains tests and examples for multiple Free API services.

## Overview

This test suite provides access to multiple free AI API services through a unified interface. Each free API service is located in its own subdirectory (free1-free6) and provides access to different AI models.

## Available Services

### free1 - OpenRouter API
- **Provider**: OpenRouter
- **Base URL**: https://openrouter.ai
- **Models**: openrouter/free, gpt-3.5-turbo, gpt-4, claude-3-opus, gemini-pro
- **Features**: Multiple model providers in one API
- **Documentation**: See [free1/README.md](free1/README.md)

### free2 - ChatAnywhere API
- **Provider**: ChatAnywhere
- **Base URL**: https://api.chatanywhere.tech
- **Models**: gpt-3.5-turbo, gpt-4o-mini, deepseek-v3
- **Features**: Free access to OpenAI-compatible API
- **Documentation**: See [free2/readme.txt](free2/readme.txt)

### free3 - Free ChatGPT API
- **Provider**: Free.v36.cm
- **Base URL**: https://free.v36.cm
- **Models**: gpt-4o-mini, gpt-3.5-turbo-0125, gpt-3.5-turbo-1106, gpt-3.5-turbo, gpt-3.5-turbo-16k
- **Features**: Free access with 200 requests/day limit
- **Documentation**: See [free3/README.md](free3/README.md)

### free4 - Mistral AI API
- **Provider**: Mistral AI
- **Base URL**: https://api.mistral.ai
- **Models**: mistral-small-latest, mistral-medium-latest, mistral-large-latest, open-mistral-nemo
- **Features**: High-performance European AI models
- **Documentation**: See [free4/README.md](free4/README.md)

### free5 - iFlow SDK API
- **Provider**: iFlow
- **Base URL**: iflow (uses SDK)
- **Models**: iflow
- **Features**: Python SDK-based API with async support
- **Documentation**: See [free5/iflow_api_proxy.py](free5/iflow_api_proxy.py)

### free6 - CSDN API
- **Provider**: CSDN
- **Base URL**: https://models.csdn.net
- **Models**: Deepseek-V3
- **Features**: Deepseek model access
- **Documentation**: See [free6/config.py](free6/config.py)

### free7 - NVIDIA API
- **Provider**: NVIDIA
- **Base URL**: https://integrate.api.nvidia.com
- **Models**: Various NVIDIA hosted models
- **Features**: High-performance GPU-accelerated inference
- **Documentation**: See [free7/README.md](free7/README.md)

### free8 - Friendli.ai API
- **Provider**: Friendli.ai
- **Base URL**: https://api.friendli.ai/serverless/v1
- **Models**: meta-llama/Llama-3.3-70B-Instruct, Qwen/Qwen3-235B-A22B-Instruct-2507, MiniMaxAI/MiniMax-M2.5, zai-org/GLM-4.7, zai-org/GLM-5
- **Features**: High-performance LLM service with OpenAI SDK compatibility
- **Documentation**: See [free8/README.md](free8/README.md)

## Requirements

- Python 3.7+
- requests library
- iflow-sdk (for free5)
- Valid API keys for respective services

## Installation

1. Install required dependencies:
```bash
pip install requests iflow-sdk
```

2. Configure API keys in the `.env` file:
```properties
FREE1_API_KEY=your_openrouter_api_key
FREE2_API_KEY=your_chatanywhere_api_key
FREE3_API_KEY=your_free_v36_api_key
FREE4_API_KEY=your_mistral_api_key
FREE5_API_KEY=your_iflow_api_key  # Optional
FREE6_API_KEY=your_csdn_api_key
```

## Usage

### Running Individual Tests

Each free API has its own test script:
```bash
cd free1
python test_api.py

cd ../free2
python test_api.py

cd ../free3
python test_api.py

cd ../free4
python test_api.py

cd ../free5
python iflow_test.py

cd ../free6
python test_api.py

cd ../free7
python test_api.py

cd ../free8
python test_api.py
```

### Using Multi API Proxy

See [multi_free_api_proxy/MULTI_FREE_API_README.md](../multi_free_api_proxy/MULTI_FREE_API_README.md) for information about using the unified proxy service that automatically manages and rotates between multiple free APIs.

## Notes

- Each free API has its own rate limits and usage quotas
- Monitor your usage through each provider's dashboard
- For production use, consider upgrading to paid plans
- Some APIs may require proxy configuration (see individual documentation)

## Multi API Proxy Integration

All free APIs (free1-free6) can be used through the multi_free_api_proxy service, which:
- Automatically detects and tests all available APIs
- Rotates between APIs for load balancing
- Handles API failures and retries
- Provides unified OpenAI-compatible interface

For more details, see the [multi_free_api_proxy documentation](../multi_free_api_proxy/).
