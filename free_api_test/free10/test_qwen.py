"""
free10_qwen - 联通云贵阳基地二区 Qwen3.5-397B-A17B API 测试脚本
"""
import os
import requests

BASE_URL = "https://aigw-gzgy2.cucloud.cn:8443"
API_KEY = os.getenv("FREE10_API_KEY")
MODEL = "Qwen3.5-397B-A17B"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 8000
TIMEOUT = 30


def read_prompt():
    """从 ask.txt 读取测试提示词"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ask_txt_path = os.path.join(script_dir, 'ask.txt')
    try:
        with open(ask_txt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("⚠ 警告：未找到 ask.txt 文件，使用默认提示词")
        return "介绍一下 Qwen3.5 模型的特点"
    except Exception as e:
        print(f"⚠ 警告：读取 ask.txt 失败：{e}，使用默认提示词")
        return "介绍一下 Qwen3.5 模型的特点"


def test_api():
    """测试 Qwen3.5-397B-A17B API"""
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
    print("free10_qwen - Qwen3.5-397B-A17B API 测试（联通云贵阳基地二区）")
    print("=" * 60)
    print()
    
    if not API_KEY or API_KEY == "<YOUR_AIMLAPI_KEY>":
        print("⚠  警告：请先在 .env 文件中配置有效的 FREE10_API_KEY")
        print()
    
    test_api()
