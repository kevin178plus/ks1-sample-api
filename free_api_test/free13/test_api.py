#!/usr/bin/env python3
"""
API 测试脚本模板
用于测试 Free API 是否可用

说明:
1. 此脚本可被 multi_free_api_proxy 调用进行健康检查
2. 支持测试模型列表和聊天完成接口
3. 自动读取 ask.txt 作为测试提示词
"""

import requests
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 从 config.py 导入配置
script_dir = Path(__file__).parent
config_path = script_dir / "config.py"

if config_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", str(config_path))
    if spec is None or spec.loader is None:
        print("[错误] 无法加载 config.py")
        sys.exit(1)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    API_KEY = config_module.API_KEY
    BASE_URL = config_module.BASE_URL
    MODEL_NAME = config_module.MODEL_NAME
    USE_PROXY = getattr(config_module, 'USE_PROXY', False)
    MAX_TOKENS = getattr(config_module, 'MAX_TOKENS', 2000)
else:
    print("[错误] 未找到 config.py 文件")
    sys.exit(1)

# 验证 API Key
if not API_KEY:
    api_key_env = f"FREE{script_dir.name.replace('free', '')}_API_KEY"
    raise ValueError(f"{api_key_env} 未在 .env 文件中配置")


def test_models_endpoint():
    """测试模型列表 API"""
    print("=" * 50)
    print("测试 1: 列出可用模型")
    print("=" * 50)

    url = f"{BASE_URL}/models"
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"状态码：{response.status_code}")

        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            print(f"[OK] 成功！找到 {len(models)} 个模型")
            print("\n部分可用模型:")
            for model in models[:5]:
                print(f"  - {model.get('id', 'unknown')}")
            return True
        else:
            print(f"[FAIL] 失败：{response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] 错误：{e}")
        return False


def test_chat_completion(model=None):
    """测试聊天完成 API"""
    print("\n" + "=" * 50)
    print(f"测试 2: 聊天完成 (模型：{model or MODEL_NAME})")
    print("=" * 50)

    url = f"{BASE_URL}/chat/completions"

    # 读取提示词
    ask_file = script_dir / 'ask.txt'
    try:
        with open(ask_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
    except Exception as e:
        print(f"[ERROR] 无法读取 ask.txt: {e}")
        prompt = "Hello, please introduce yourself."

    payload = {
        "model": model or MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": min(MAX_TOKENS, 1000)
    }

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"状态码：{response.status_code}")

        if response.status_code == 200:
            data = response.json()
            
            # 提取内容（根据 RESPONSE_FORMAT 配置）
            choice = data.get('choices', [{}])[0]
            message = choice.get('message', {})
            
            # 尝试多个可能的内容字段
            content = None
            for field in ['content', 'reasoning_content']:
                content = message.get(field)
                if content:
                    break
            
            if not content:
                content = str(message)
            
            usage = data.get('usage', {})

            print(f"[OK] 成功！")
            print(f"\n使用的 Token:")
            print(f"  - 输入：{usage.get('prompt_tokens', 'N/A')}")
            print(f"  - 输出：{usage.get('completion_tokens', 'N/A')}")
            print(f"  - 总计：{usage.get('total_tokens', 'N/A')}")

            # 写入结果文件
            result_file = script_dir / 'test_result.txt'
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write("API 测试结果\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"模型：{model or MODEL_NAME}\n")
                f.write(f"输入 Token: {usage.get('prompt_tokens', 'N/A')}\n")
                f.write(f"输出 Token: {usage.get('completion_tokens', 'N/A')}\n")
                f.write(f"总计 Token: {usage.get('total_tokens', 'N/A')}\n\n")
                f.write("生成的回复:\n")
                f.write("-" * 50 + "\n")
                f.write(content)
                f.write("\n" + "-" * 50 + "\n")

            print(f"\n[OK] 结果已保存到 {result_file}")
            return True
        else:
            print(f"[FAIL] 失败：{response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] 错误：{e}")
        return False


def main():
    """主函数"""
    print(f"API 有效性测试 - {Path(__file__).parent.name}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:] if len(API_KEY) > 10 else API_KEY}")
    print(f"Base URL: {BASE_URL}\n")

    results = []

    # 测试 1: 模型列表（如果 API 支持）
    try:
        results.append(("模型列表", test_models_endpoint()))
    except Exception as e:
        print(f"[跳过] 模型列表测试失败：{e}")
        results.append(("模型列表", False))

    # 测试 2: 聊天完成
    results.append(("聊天完成", test_chat_completion()))

    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)

    for name, result in results:
        status = "[PASS] 通过" if result else "[FAIL] 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)
    print(f"\n总体：{'[PASS] 所有测试通过' if all_passed else '[FAIL] 部分测试失败'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
