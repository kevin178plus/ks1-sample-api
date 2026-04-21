#!/usr/bin/env python3
"""
free14 - CGC ChanCloud AI API 测试脚本
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import requests
import truststore

script_dir = Path(__file__).parent
load_dotenv(script_dir / ".env")

API_KEY = os.getenv("FREE14_API_KEY")
BASE_URL = "https://cgc.chancloud.com/cgc/api/public/ai/server"
MODEL_NAME = "Nemotron-3-Super-120B-A12B"
MAX_TOKENS = 1024

class SSLContextAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = truststore.SSLContext()
        kwargs['ssl_context'] = ctx
        super().init_poolmanager(*args, **kwargs)


def read_prompt():
    ask_file = script_dir / 'ask.txt'
    try:
        with open(ask_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print("! 警告：未找到 ask.txt 文件，使用默认提示词")
        return "Hello, how are you?"
    except Exception as e:
        print(f"! 警告：读取 ask.txt 失败：{e}，使用默认提示词")
        return "Hello, how are you?"


def parse_sse_stream(text):
    content = ""
    for line in text.split('\n'):
        if line.startswith('data:') or line.startswith('data: '):
            data = line[5:].strip()
            if data and data != '[DONE]':
                try:
                    json_data = json.loads(data)
                    if 'choices' in json_data and len(json_data['choices']) > 0:
                        delta = json_data['choices'][0].get('delta', {})
                        if 'content' in delta and delta['content']:
                            content += delta['content']
                except json.JSONDecodeError:
                    pass
    return content


def test_api():
    prompt = read_prompt()
    url = f"{BASE_URL}/chat/stream"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "top_p": 1,
        "max_tokens": MAX_TOKENS,
        "stream": True
    }

    try:
        session = requests.Session()
        session.mount('https://', SSLContextAdapter())

        print(f"请求 URL: {url}")
        print(f"模型: {MODEL_NAME}")
        print(f"提示词: {prompt[:50]}..." if len(prompt) > 50 else f"提示词: {prompt}")
        print("-" * 50)

        stream_response = session.post(url, headers=headers, json=data, stream=True, timeout=120)

        print(f"状态码: {stream_response.status_code}")

        result_text = ""
        for chunk in stream_response.iter_lines():
            if chunk:
                result_text += chunk.decode('utf-8') + "\n"

        if stream_response.headers.get('content-type', '').startswith('text/event-stream'):
            content = parse_sse_stream(result_text)
        else:
            try:
                result = json.loads(result_text)
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                else:
                    print(f"! 响应格式异常: {result}")
                    return False
            except json.JSONDecodeError:
                print(f"! 无法解析响应: {result_text[:200]}")
                return False

        print(f"\n+ 请求成功")
        print(f"AI 回复:")
        print("-" * 50)
        try:
            print(content)
        except UnicodeEncodeError:
            print("[内容包含非GBK字符，已保存到文件]")
        print("-" * 50)

        save_result(prompt, content)
        return True

    except requests.exceptions.Timeout:
        print("X 请求超时")
        return False
    except requests.exceptions.RequestException as e:
        print(f"X 请求失败：{e}")
        return False
    except KeyError as e:
        print(f"X 响应格式错误：{e}")
        return False
    except Exception as e:
        print(f"X 未知错误：{e}")
        return False


def save_result(prompt, content):
    result_path = script_dir / 'test_result.txt'

    try:
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("CGC ChanCloud AI API 测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"模型: {MODEL_NAME}\n\n")
            f.write("提示词:\n")
            f.write("-" * 50 + "\n")
            f.write(prompt)
            f.write("\n" + "-" * 50 + "\n\n")
            f.write("AI 回复:\n")
            f.write("-" * 50 + "\n")
            f.write(content)
            f.write("\n" + "-" * 50 + "\n")

        print(f"\n+ 结果已保存到 test_result.txt")
    except Exception as e:
        print(f"\n! 保存结果失败：{e}")


if __name__ == "__main__":
    print("=" * 60)
    print("free14 - CGC ChanCloud AI API 测试")
    print("=" * 60)
    print()
    print(f"API 地址: {BASE_URL}")
    print(f"模型: {MODEL_NAME}")
    print()

    if not API_KEY:
        print("! 警告：请先在 .env 文件中配置 FREE14_API_KEY")
        print()

    success = test_api()
    sys.exit(0 if success else 1)
