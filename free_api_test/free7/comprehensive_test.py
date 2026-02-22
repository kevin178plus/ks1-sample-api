
import os
import requests
from config import API_KEY, BASE_URL, MODEL_NAME

def load_question(filepath):
    """从文件中读取问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def test_configuration(test_name, thinking, enable_thinking, clear_thinking):
    """测试特定配置"""
    print("\n" + "="*60)
    print("测试: " + test_name)
    print("="*60)

    # 从 ask.txt 读取问题
    try:
        question = load_question('ask.txt')
        print("✓ 成功读取问题 (共 " + str(len(question)) + " 字符)")
    except Exception as e:
        print("✗ 读取 ask.txt 失败: " + str(e))
        return False

    headers = {
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": question}
        ],
        "max_tokens": 2048,  # 增加token限制
        "temperature": 0.20,
        "top_p": 1.00,
        "stream": False,
    }

    # 添加 chat_template_kwargs
    if thinking is not None:
        data["chat_template_kwargs"] = {"thinking": thinking}
    elif enable_thinking is not None or clear_thinking is not None:
        kwargs = {}
        if enable_thinking is not None:
            kwargs["enable_thinking"] = enable_thinking
        if clear_thinking is not None:
            kwargs["clear_thinking"] = clear_thinking
        data["chat_template_kwargs"] = kwargs

    print("chat_template_kwargs: " + str(data.get("chat_template_kwargs", "None")))

    # 配置代理
    proxies = None
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    if http_proxy:
        proxies = {
            "http": http_proxy,
            "https": http_proxy
        }
        print("✓ 使用代理: " + http_proxy)

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
        message = result['choices'][0].get('message', {})
        content = message.get('content')
        reasoning_content = message.get('reasoning_content')

        print("\n--- 返回内容分析 ---")
        print("content 是否存在: " + str(content is not None))
        if content:
            print("content 长度: " + str(len(content)))
            print("content 前100字符: " + content[:100])

        print("\nreasoning_content 是否存在: " + str(reasoning_content is not None))
        if reasoning_content:
            print("reasoning_content 长度: " + str(len(reasoning_content)))
            print("reasoning_content 前100字符: " + reasoning_content[:100])

        print("\nfinish_reason: " + result['choices'][0].get('finish_reason', 'unknown'))
        print("matched_stop: " + str(result['choices'][0].get('matched_stop')))

        # 保存结果
        output_file = 'test_result_' + test_name.replace(' ', '_') + '.txt'
        if content:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== CONTENT ===\n\n")
                f.write(content)
        if reasoning_content:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write("\n\n=== REASONING_CONTENT ===\n\n")
                f.write(reasoning_content)
        print("✓ 结果已写入: " + output_file)

        return True
    except Exception as e:
        print("✗ API 调用失败: " + str(e))
        return False

def run_all_tests():
    """运行所有测试配置"""
    print("开始多角度测试...")

    # 测试1: thinking=False
    test_configuration(
        test_name="thinking_False",
        thinking=False,
        enable_thinking=None,
        clear_thinking=None
    )

    # 测试2: thinking=True
    test_configuration(
        test_name="thinking_True",
        thinking=True,
        enable_thinking=None,
        clear_thinking=None
    )

    # 测试3: enable_thinking=True, clear_thinking=False
    test_configuration(
        test_name="enable_thinking_True_clear_thinking_False",
        thinking=None,
        enable_thinking=True,
        clear_thinking=False
    )

    # 测试4: 不设置 chat_template_kwargs
    test_configuration(
        test_name="no_chat_template_kwargs",
        thinking=None,
        enable_thinking=None,
        clear_thinking=None
    )

    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)

if __name__ == "__main__":
    run_all_tests()
