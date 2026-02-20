
"""
测试 free1 API
"""
import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量读取 API Key
FREE1_API_KEY = os.getenv("FREE1_API_KEY")
HTTP_PROXY = os.getenv("HTTP_PROXY")

if not FREE1_API_KEY:
    print("错误: FREE1_API_KEY 环境变量未设置")
    print("请确保 .env 文件中包含 FREE1_API_KEY=sk-or-v1-e38xxxxxxxxxxxxxx2")
    exit(1)

# API 配置
BASE_URL = "https://openrouter.ai"
MODEL = "openrouter/free"
USE_PROXY = True  # free1 需要使用代理

print(f"测试 free1 API")
print(f"Base URL: {BASE_URL}")
print(f"Model: {MODEL}")
print(f"API Key: {FREE1_API_KEY[:10]}...{FREE1_API_KEY[-4:]}")
print("-" * 50)

# 测试请求
url = f"{BASE_URL}/v1/chat/completions"
headers = {
    'Authorization': f'Bearer {FREE1_API_KEY}',
    'Content-Type': 'application/json'
}

# 配置代理
proxies = None
if USE_PROXY and HTTP_PROXY:
    proxies = {
        "http": HTTP_PROXY,
        "https": HTTP_PROXY
    }
    print(f"使用代理: {HTTP_PROXY}")

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "你好，请用一句话介绍你自己"}
    ],
    "max_tokens": 100
}

print("发送测试请求...")
try:
    response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=30)

    print(f"状态码: {response.status_code}")
    print(f"原始响应: {response.text[:500]}")  # 打印前500个字符

    if response.status_code == 200:
        try:
            result = response.json()
            print("✓ 测试成功!")
            print(f"响应: {result['choices'][0]['message']['content']}")
        except Exception as e:
            print(f"✗ 解析响应失败: {e}")
    else:
        print(f"✗ 测试失败")
        print(f"错误信息: {response.text}")
except Exception as e:
    print(f"✗ 请求异常: {e}")
