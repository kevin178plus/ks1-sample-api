"""
free10 - AIML API 测试脚本（使用联通云贵阳基地二区 API）
"""
import requests
from config import BASE_URL, API_KEY, MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, TIMEOUT


def read_prompt():
    """从 ask.txt 读取测试提示词"""
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("⚠ 警告：未找到 ask.txt 文件，使用默认提示词")
        return "Tell me about San Francisco"
    except Exception as e:
        print(f"⚠ 警告：读取 ask.txt 失败：{e}，使用默认提示词")
        return "Tell me about San Francisco"


def test_api():
    """测试 AIML API"""
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
    print("free10 - AIML API 测试（联通云贵阳基地二区）")
    print("=" * 60)
    print()
    
    # 检查 API Key 配置
    if not API_KEY or API_KEY == "<YOUR_AIMLAPI_KEY>":
        print("⚠  警告：请先在 config.py 中配置有效的 API_KEY")
        print()
    
    # 运行测试
    test_api()
