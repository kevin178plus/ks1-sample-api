import os
import requests
from config import API_KEY, BASE_URL, MODEL_NAME

def load_question(filepath):
    """从文件中读取问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def save_result(filepath, content):
    """将结果写入文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def test_api():
    if not API_KEY:
        print("✗ 错误: 未找到 FREE7_API_KEY 环境变量")
        print("请在 .env 文件中设置: FREE7_API_KEY=your_api_key")
        return False

    print("API_KEY:", API_KEY[:5] + "..." if API_KEY else "None")

    # 从 ask.txt 读取问题
    try:
        question = load_question('ask.txt')
        print(f"✓ 成功读取问题 (共 {len(question)} 字符)")
    except Exception as e:
        print(f"✗ 读取 ask.txt 失败: {e}")
        return False

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": question}
        ],
        "max_tokens": 4096,
        "temperature": 0.20,
        "top_p": 1.00,
        "stream": False,
        "chat_template_kwargs": {"thinking": False}
    }

    # 配置代理
    proxies = None
    # http_proxy = os.getenv("HTTP_PROXY")
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    if http_proxy:
        proxies = {
            "http": http_proxy,
            "https": http_proxy
        }
        print(f"✓ 使用代理: {http_proxy}")

    try:
        print("正在调用 API...")
        response = requests.post(
            BASE_URL + "v1/chat/completions",
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        print("✓ API 调用成功！")
        print("✓ 响应数据结构: " + str(list(result.keys())))

        # 提取回答内容
        try:
            # 检查返回的数据结构
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                content = message.get('content')
                reasoning_content = message.get('reasoning_content')

                # 优先使用 content，如果为 None 则使用 reasoning_content
                if content is not None:
                    answer = content
                elif reasoning_content is not None:
                    answer = reasoning_content
                    print("✓ 注意: content 为 None，使用 reasoning_content")
                else:
                    print("✗ 错误: content 和 reasoning_content 都为 None")
                    print("✓ 完整响应数据:")
                    print(result)
                    return False

                # 保存结果到 test_result.txt
                save_result('test_result.txt', answer)
                print(f"✓ 结果已写入 test_result.txt (共 {len(answer)} 字符)")
                return True
            else:
                print("✗ 错误: 返回数据中没有 choices 字段")
                print("✓ 完整响应数据:")
                print(result)
                return False
        except Exception as e:
            print(f"✗ 提取回答内容失败: {e}")
            print("✓ 完整响应数据:")
            print(result)
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ API 调用失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"错误详情: {e.response.text}")
        return False

if __name__ == "__main__":
    test_api()
