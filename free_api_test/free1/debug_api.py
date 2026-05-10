import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("FREE1_API_KEY")
print(f"API Key: {api_key[:15]}...")

# 测试 models 接口
url = "https://openrouter.ai/api/v1/models"
headers = {'Authorization': f'Bearer {api_key}'}

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"\n状态码: {response.status_code}")
    print(f"响应: {response.text[:1000]}")
except Exception as e:
    print(f"错误: {e}")
