import requests
import json

# 测试本地代理
BASE_URL = "http://localhost:5000"

print("=" * 50)
print("测试本地 API 代理")
print("=" * 50)

# 1. 健康检查
print("\n1. 健康检查...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态: {response.json()}")
except Exception as e:
    print(f"错误: {e}")

# 2. 列出模型
print("\n2. 列出可用模型...")
try:
    response = requests.get(f"{BASE_URL}/v1/models")
    print(f"模型: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"错误: {e}")

# 3. 测试聊天完成
print("\n3. 测试聊天完成...")
try:
    payload = {
        "messages": [
            {"role": "user", "content": "Hello! What can you help me with today?"}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload)
    result = response.json()
    
    if "error" in result:
        print(f"错误: {result['error']}")
    else:
        print(f"模型: {result.get('model')}")
        print(f"回复: {result['choices'][0]['message']['content']}")
        print(f"使用量: {result.get('usage')}")
except Exception as e:
    print(f"错误: {e}")

print("\n" + "=" * 50)
