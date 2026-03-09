"""
free12 - OpenCode AI API 测试脚本
"""
import os
import sys
import requests
from config import BASE_URL, API_KEY, MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS, TIMEOUT


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
    """测试 OpenCode AI API"""
    # 读取测试提示词
    prompt = read_prompt()

    url = f"{BASE_URL}/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
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
        print(f"请求 URL: {url}")
        print(f"模型: {MODEL_NAME}")
        print(f"提示词: {prompt[:50]}..." if len(prompt) > 50 else f"提示词: {prompt}")
        print("-" * 50)
        
        response = requests.post(url, headers=headers, json=data, timeout=TIMEOUT)
        response.raise_for_status()

        result = response.json()
        
        # 处理响应
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
        else:
            print(f"⚠ 响应格式异常: {result}")
            return False

        print(f"\n✓ 请求成功")
        print(f"AI 回复:")
        print("-" * 50)
        print(content)
        print("-" * 50)
        
        # 显示使用统计
        if "usage" in result:
            print(f"\n使用统计：")
            print(f"  - 输入 tokens: {result['usage'].get('prompt_tokens', 'N/A')}")
            print(f"  - 输出 tokens: {result['usage'].get('completion_tokens', 'N/A')}")
            print(f"  - 总计 tokens: {result['usage'].get('total_tokens', 'N/A')}")

        # 保存结果到文件
        save_result(prompt, content, result)
        
        return True

    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求失败：{e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应内容: {e.response.text}")
        return False
    except KeyError as e:
        print(f"✗ 响应格式错误：{e}")
        return False
    except Exception as e:
        print(f"✗ 未知错误：{e}")
        return False


def save_result(prompt, content, result):
    """保存测试结果到文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(script_dir, 'test_result.txt')
    
    try:
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("OpenCode AI API 测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"模型: {MODEL_NAME}\n")
            f.write(f"时间: {result.get('created', 'N/A')}\n\n")
            
            if "usage" in result:
                f.write("使用统计:\n")
                f.write(f"  - 输入 tokens: {result['usage'].get('prompt_tokens', 'N/A')}\n")
                f.write(f"  - 输出 tokens: {result['usage'].get('completion_tokens', 'N/A')}\n")
                f.write(f"  - 总计 tokens: {result['usage'].get('total_tokens', 'N/A')}\n\n")
            
            f.write("提示词:\n")
            f.write("-" * 50 + "\n")
            f.write(prompt)
            f.write("\n" + "-" * 50 + "\n\n")
            
            f.write("AI 回复:\n")
            f.write("-" * 50 + "\n")
            f.write(content)
            f.write("\n" + "-" * 50 + "\n")
        
        print(f"\n✓ 结果已保存到 test_result.txt")
    except Exception as e:
        print(f"\n⚠ 保存结果失败：{e}")


if __name__ == "__main__":
    print("=" * 60)
    print("free12 - OpenCode AI API 测试")
    print("=" * 60)
    print()
    print(f"API 地址: {BASE_URL}")
    print(f"模型: {MODEL_NAME}")
    print()

    # 检查 API Key 配置
    if not API_KEY or API_KEY == "your_api_key_here":
        print("⚠ 警告：请先在 config.py 中配置有效的 API_KEY")
        print()

    # 运行测试
    success = test_api()
    sys.exit(0 if success else 1)
