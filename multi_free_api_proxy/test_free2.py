
"""
测试 free2 API
"""
import os
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从环境变量读取 API Key
FREE2_API_KEY = os.getenv("FREE2_API_KEY")

if not FREE2_API_KEY:
    print("错误: FREE2_API_KEY 环境变量未设置")
    print("请确保 .env 文件中包含 FREE2_API_KEY=sk-RJexxxxxxxxxxx")
    exit(1)

# API 配置
BASE_URL = "https://api.chatanywhere.tech"
MODEL = "gpt-3.5-turbo"

print(f"测试 free2 API")
print(f"Base URL: {BASE_URL}")
print(f"Model: {MODEL}")
print(f"API Key: {FREE2_API_KEY[:10]}...{FREE2_API_KEY[-4:]}")
print("-" * 50)

# 测试请求
url = f"{BASE_URL}/v1/chat/completions"
headers = {
    'Authorization': f'Bearer {FREE2_API_KEY}',
    'Content-Type': 'application/json'
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "你好，请用一句话介绍你自己"}
    ],
    "max_tokens": 100
}

print("发送测试请求...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("✓ 测试成功!")
        print(f"响应: {result['choices'][0]['message']['content']}")
    else:
        print(f"✗ 测试失败")
        print(f"错误信息: {response.text}")
except Exception as e:
    print(f"✗ 请求异常: {e}")
