#!/usr/bin/env python3
"""
测试小米 MiMo API 连接
"""
import os
import sys
import requests
from dotenv import load_dotenv

# 加载 .env 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(project_dir, '.env'))


def test_mimo_api():
    """测试小米 MiMo API 是否可用"""
    api_key = os.getenv("FREE23_API_KEY")

    if not api_key:
        print("[ERROR] 未找到 FREE23_API_KEY")
        print("请在 .env 文件中设置 FREE23_API_KEY")
        return False

    print(f"[OK] 找到 API Key (前缀: {api_key[:20]}...)")

    url = "https://api.xiaomimimo.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mimo-v2.5-pro",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 10
    }

    print("Testing Xiaomi MiMo API...")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print("[OK] API 连接成功!")
            print(f"   模型: {result.get('model', 'N/A')}")
            choices = result.get('choices', [])
            if choices:
                print(f"   内容: {choices[0].get('message', {}).get('content', 'N/A')}")
            return True
        else:
            print(f"[FAIL] API 连接失败: {response.status_code}")
            print(f"   响应: {response.text[:500]}")
            return False
    except requests.exceptions.Timeout:
        print("[TIMEOUT] 请求超时")
        return False
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Xiaomi MiMo API Test (free23)")
    print("=" * 60)

    success = test_mimo_api()

    print(f"\n{'=' * 60}")
    print(f"Result: {'✅ PASS' if success else '❌ FAIL'}")
    sys.exit(0 if success else 1)
