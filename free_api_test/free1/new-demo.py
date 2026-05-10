#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenRouter API 简单演示
使用 OpenAI SDK 调用 OpenRouter API
"""
import sys
import io

# 设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import httpx
from dotenv import load_dotenv
from openai import OpenAI

# 加载环境变量（从项目根目录加载）
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

# 获取 API Key
API_KEY = os.getenv("FREE1_API_KEY")
if not API_KEY:
    raise ValueError("FREE1_API_KEY not found in .env file")

# 获取代理配置
HTTP_PROXY = os.getenv("HTTP_PROXY")

# 配置 httpx 客户端（支持代理）
http_client = None
if HTTP_PROXY:
    http_client = httpx.Client(proxy=HTTP_PROXY)

# 创建客户端
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    http_client=http_client,
)

# 读取提示词
try:
    with open('ask.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()
except Exception as e:
    print(f"[ERROR] 无法读取 ask.txt: {e}")
    prompt = "What is the meaning of life?"

try:
    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "Free API Demo",
        },
        model="openrouter/free",  # 使用免费模型
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=1000
    )

    content = completion.choices[0].message.content
    usage = completion.usage

    print("=" * 50)
    print("API 调用成功!")
    print("=" * 50)
    print(f"\n使用的 Token:")
    print(f"  - 输入: {usage.prompt_tokens}")
    print(f"  - 输出: {usage.completion_tokens}")
    print(f"  - 总计: {usage.total_tokens}")
    print(f"\n生成的回复:")
    print("-" * 50)
    print(content)
    print("-" * 50)

except Exception as e:
    print(f"[ERROR] API 调用失败: {e}")
