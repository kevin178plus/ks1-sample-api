import os
import requests

# 从环境变量读取配置
API_KEY = os.getenv("FREE6_API_KEY")
API_URL = "https://models.csdn.net/v1/chat/completions"
MODEL_NAME = "Deepseek-V3"

def test_api():
    if not API_KEY:
        print("✗ 错误: 未找到 FREE6_API_KEY 环境变量")
        print("请在 .env 文件中设置: FREE6_API_KEY=your_api_key")
        return False

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "你好，请回复一个简单的测试消息"}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        print("✓ API 测试成功！")
        print(f"响应内容: {result['choices'][0]['message']['content']}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ API 测试失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"错误详情: {e.response.text}")
        return False

if __name__ == "__main__":
    test_api()
