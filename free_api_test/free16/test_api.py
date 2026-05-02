#!/usr/bin/env python3
"""
测试 Sambanova API 连接
"""
import os
import sys
import requests
from dotenv import load_dotenv

# 加载 .env 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(project_dir, '.env'))

def test_sambanova_api():
    """测试Sambanova API是否可用"""
    api_key = os.getenv("SAMBANOVA_API_KEY")
    
    if not api_key:
        print("[ERROR] 未找到 SAMBANOVA_API_KEY")
        print("请在 .env 文件中设置 SAMBANOVA_API_KEY")
        return False
    
    print(f"[OK] 找到 API Key (前缀: {api_key[:20]}...)")
    
    url = "https://api.sambanova.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "DeepSeek-V3.1",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 10
    }
    
    print("Testing API connection...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("[OK] API 连接成功!")
            print(f"   模型: {result.get('model', 'N/A')}")
            print(f"   内容: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
            return True
        else:
            print(f"[FAIL] API 连接失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[TIMEOUT] 请求超时")
        return False
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False

def list_models():
    """列出可用模型"""
    api_key = os.getenv("SAMBANOVA_API_KEY")
    
    if not api_key:
        print("[ERROR] 未找到 SAMBANOVA_API_KEY")
        return
    
    url = "https://api.sambanova.ai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("\nAvailable Models:")
            print("-" * 60)
            for model in result.get('data', []):
                model_id = model.get('id', 'N/A')
                print(f"  * {model_id}")
        else:
            print(f"[FAIL] 获取模型列表失败: {response.status_code}")
            
    except Exception as e:
        print(f"[FAIL] 获取模型列表失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Sambanova API Test")
    print("=" * 60)
    
    success = test_sambanova_api()
    
    if success:
        print("\n" + "=" * 60)
        list_models()
    
    sys.exit(0 if success else 1)
