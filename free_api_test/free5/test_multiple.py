import requests
import json

url = "http://localhost:5005/v1/chat/completions"
headers = {"Content-Type": "application/json"}

test_cases = [
    {"role": "user", "content": "法国的首都是哪里？"},
    {"role": "user", "content": "用一句话介绍Python"},
    {"role": "user", "content": "今天天气怎么样？"},
    {"role": "user", "content": "写一个简单的Python函数"},
    {"role": "user", "content": "什么是人工智能？"}
]

print("开始批量测试...\n")

for i, message in enumerate(test_cases, 1):
    print(f"测试 {i}/{len(test_cases)}: {message['content']}")
    data = {
        "model": "iflow",
        "messages": [message]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"  ✓ 成功: {content[:50]}{'...' if len(content) > 50 else ''}")
        else:
            print(f"  ✗ 失败 (状态码: {response.status_code}): {response.text[:100]}")
    except Exception as e:
        print(f"  ✗ 异常: {e}")

    print()

print("批量测试完成!")