import os
import requests

# 从环境变量读取配置
API_KEY = os.getenv("FREE9_API_KEY")
BASE_URL = "https://ark.cn-beijing.volces.com/api/coding"
ENDPOINT = "/v3/chat/completions"
MODEL_NAME = "ark-code-latest"

def read_prompt():
    """从 ask.txt 读取测试提示词"""
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("⚠ 警告：未找到 ask.txt 文件，使用默认提示词")
        return "你好，请回复一个简单的测试消息"
    except Exception as e:
        print(f"⚠ 警告：读取 ask.txt 失败：{e}，使用默认提示词")
        return "你好，请回复一个简单的测试消息"

def test_api():
    if not API_KEY:
        print("✗ 错误：未找到 FREE9_API_KEY 环境变量")
        print("请在 .env 文件中设置：FREE9_API_KEY=your_api_key")
        return False

    # 读取测试提示词
    prompt = read_prompt()

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        url = f"{BASE_URL}{ENDPOINT}"
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        print("✓ API 测试成功！")
        print(f"使用的提示词：{prompt[:50]}..." if len(prompt) > 50 else f"使用的提示词：{prompt}")
        print(f"响应内容：{content}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ API 测试失败：{e}")
        if hasattr(e, 'response') and e.response:
            print(f"错误详情：{e.response.text}")
        return False

if __name__ == "__main__":
    test_api()
