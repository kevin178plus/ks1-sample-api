#!/usr/bin/env python3
"""
测试 Cohere API 连接
"""
import os
import sys
import requests
from dotenv import load_dotenv

# 加载 .env 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(project_dir, '.env'))

def test_cohere_api():
    """测试Cohere API是否可用"""
    api_key = os.getenv("COHERE_API_KEY")
    
    if not api_key:
        print("[ERROR] 未找到 COHERE_API_KEY")
        print("请在 .env 文件中设置 COHERE_API_KEY")
        return False
    
    print(f"[OK] 找到 API Key (前缀: {api_key[:20]}...)")
    
    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": "command-a-03-2025",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.3
    }
    
    print("Testing without proxy...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] API 连接成功! (无代理)")
            print(f"   响应: {result}")
            return True
        else:
            print(f"[FAIL] API 连接失败 (无代理): {response.status_code}")
            print(f"   响应: {response.text[:200]}...")
    except requests.exceptions.Timeout:
        print("[TIMEOUT] 请求超时 (无代理)")
    except Exception as e:
        print(f"[FAIL] 测试失败 (无代理): {e}")
    
    # 测试使用代理
    print("\nTesting with proxy (127.0.0.1:7897)...")
    proxies = {
        "http": "http://127.0.0.1:7897",
        "https": "http://127.0.0.1:7897"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] API 连接成功! (使用代理)")
            print(f"   响应: {result}")
            return True
        else:
            print(f"[FAIL] API 连接失败 (使用代理): {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("[TIMEOUT] 请求超时 (使用代理)")
        return False
    except Exception as e:
        print(f"[FAIL] 测试失败 (使用代理): {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Cohere API Test")
    print("=" * 60)
    
    success = test_cohere_api()
    
    sys.exit(0 if success else 1)