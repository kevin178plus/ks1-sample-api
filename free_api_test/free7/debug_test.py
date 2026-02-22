
import os
import requests
from config import API_KEY, BASE_URL, MODEL_NAME

def load_question(filepath):
    """从文件中读取问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def test_configuration(test_name, use_proxy, chat_template_kwargs, api_key=None, base_url=None, model_name=None):
    """测试特定配置"""
    print("\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")

    # 使用提供的参数或默认配置
    current_api_key = api_key or API_KEY
    current_base_url = base_url or BASE_URL
    current_model = model_name or MODEL_NAME

    print(f"API Key: {current_api_key[:5]}..." if current_api_key else "None")
    print(f"Base URL: {current_base_url}")
    print(f"Model: {current_model}")
    print(f"Use Proxy: {use_proxy}")
    print(f"Chat Template: {chat_template_kwargs}")

    # 从 ask.txt 读取问题
    try:
        question = load_question('ask.txt')
        print(f"✓ 成功读取问题 (共 {len(question)} 字符)")
    except Exception as e:
        print(f"✗ 读取 ask.txt 失败: {e}")
        return False

    headers = {
        "Authorization": f"Bearer {current_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "model": current_model,
        "messages": [
            {"role": "user", "content": question}
        ],
        "max_tokens": 1024,
        "temperature": 0.20,
        "top_p": 1.00,
        "stream": False,
    }

    # 添加 chat_template_kwargs（如果提供）
    if chat_template_kwargs is not None:
        data["chat_template_kwargs"] = chat_template_kwargs

    # 配置代理
    proxies = None
    if use_proxy:
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
            current_base_url + "v1/chat/completions",
            headers=headers,
            json=data,
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        print("✓ API 调用成功！")
        print("✓ 完整响应: " + str(result))

        # 提取回答内容
        try:
            answer = result['choices'][0]['message']['content']
            print("✓ 回答长度: " + str(len(answer)) + " 字符")
            print("✓ 回答预览: " + answer[:100] + "...")
            return True
        except Exception as e:
            print("✗ 提取回答内容失败: " + str(e))
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ API 调用失败: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"错误详情: {e.response.text}")
        return False

def run_all_tests():
    """运行所有测试配置"""
    print("开始测试各种配置组合...")

    # 测试1: 原始配置（使用代理，thinking=False）
    test_configuration(
        test_name="原始配置（使用代理，thinking=False）",
        use_proxy=True,
        chat_template_kwargs={"thinking": False}
    )

    # 测试2: 不使用代理，thinking=False
    test_configuration(
        test_name="不使用代理，thinking=False",
        use_proxy=False,
        chat_template_kwargs={"thinking": False}
    )

    # 测试3: 不使用代理，thinking=True
    test_configuration(
        test_name="不使用代理，thinking=True",
        use_proxy=False,
        chat_template_kwargs={"thinking": True}
    )

    # 测试4: 使用代理，thinking=True
    test_configuration(
        test_name="使用代理，thinking=True",
        use_proxy=True,
        chat_template_kwargs={"thinking": True}
    )

    # 测试5: 不使用代理，不设置 chat_template_kwargs
    test_configuration(
        test_name="不使用代理，不设置 chat_template_kwargs",
        use_proxy=False,
        chat_template_kwargs=None
    )

    # 测试6: 使用 demo.py 中的 API key
    test_configuration(
        test_name="使用 demo.py 的 API key，不使用代理",
        use_proxy=False,
        chat_template_kwargs={"thinking": True},
        api_key="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"
    )

    # 测试7: 使用 demo2.py 中的 API key
    test_configuration(
        test_name="使用 demo2.py 的 API key，不使用代理",
        use_proxy=False,
        chat_template_kwargs=None,
        api_key="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"
    )

    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
