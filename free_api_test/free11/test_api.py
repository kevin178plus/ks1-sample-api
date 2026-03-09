"""
free11 - 白山智算 API 测试脚本
"""
import os
import requests
from config import BASE_URL, API_KEY, MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, TIMEOUT


def read_prompt():
    """从 ask.txt 读取测试提示词"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ask_txt_path = os.path.join(script_dir, 'ask.txt')
    try:
        with open(ask_txt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("⚠ 警告：未找到 ask.txt 文件，使用默认提示词")
        return "Hello, how are you?"
    except Exception as e:
        print(f"⚠ 警告：读取 ask.txt 失败：{e}，使用默认提示词")
        return "Hello, how are you?"


def test_api():
    """测试白山智算 API"""
    # 读取测试提示词
    prompt = read_prompt()

    url = f"{BASE_URL}/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        print(f"✓ 请求成功")
        print(f"模型：{MODEL}")
        print(f"使用的提示词：{prompt[:50]}..." if len(prompt) > 50 else f"使用的提示词：{prompt}")
        print(f"AI: {content}")
        print(f"\n使用统计：")
        print(f"  - 输入 tokens: {result['usage']['prompt_tokens']}")
        print(f"  - 输出 tokens: {result['usage']['completion_tokens']}")
        print(f"  - 总计 tokens: {result['usage']['total_tokens']}")

        return True

    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求失败：{e}")
        return False
    except KeyError as e:
        print(f"✗ 响应格式错误：{e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("free11 - 白山智算 API 测试")
    print("=" * 60)
    print()

    # 检查 API Key 配置
    if not API_KEY or API_KEY == "your_api_key_here":
        print("⚠  警告：请先在 config.py 中配置有效的 API_KEY")
        print()

    # 运行测试
    test_api()