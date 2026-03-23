import requests
import json

url = "http://localhost:5005/v1/chat/completions"
headers = {"Content-Type": "application/json"}
data = {
    "model": "iflow",
    "messages": [
        {"role": "user", "content": "1+1等于多少？"}
    ]
}

print("发送请求到 API...")
response = requests.post(url, headers=headers, json=data, timeout=60)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")

if response.status_code == 200:
    result = response.json()
    print("\n成功!")
    print(f"模型: {result.get('model')}")
    print(f"内容: {result.get('choices', [{}])[0].get('message', {}).get('content')}")
else:
    print("\n失败!")
    print(f"错误: {response.text}")