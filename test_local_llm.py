"""
测试本地 LLM 服务 (localhost:20128)
"""
import requests
import json
import sys
from datetime import datetime

# Windows GBK 兼容
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_llm_service(url="http://localhost:20128/v1/chat/completions"):
    """测试 LLM 服务"""

    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始测试 LLM 服务: {url}")
    print("=" * 60)

    # 测试请求
    payload = {
        "model": "minimax-m2.7",
        "messages": [
            {"role": "user", "content": "你好，回复 'OK' 即可"}
        ],
        "max_tokens": 100,
        "temperature": 0.1
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 发送测试请求...")
        print(f"Payload: model={payload['model']}, max_tokens={payload['max_tokens']}")

        start_time = datetime.now()
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 响应时间: {elapsed:.2f}s")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 状态码: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 请求成功!")

                if "choices" in result:
                    content = result["choices"][0]["message"]["content"]
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 模型: {result.get('model', 'unknown')}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 回复: {content[:200]}")

                    # 显示 usage
                    if "usage" in result:
                        usage = result["usage"]
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Usage: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}, total={usage.get('total_tokens', 0)}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 响应内容: {result}")

            except json.JSONDecodeError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] 响应不是有效 JSON")
                print(f"Raw: {response.text[:500]}")

        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] 请求失败!")
            try:
                error = response.json()
                print(f"Error: {json.dumps(error, indent=2, ensure_ascii=False)}")
            except:
                print(f"Raw: {response.text[:500]}")

        return response.status_code == 200

    except requests.exceptions.Timeout:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] 请求超时 (60s)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] 连接失败: {e}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 提示: 确保服务在 {url} 运行")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] 错误: {e}")
        return False


def test_models_endpoint(base_url="http://localhost:20128"):
    """测试 /v1/models 接口"""
    url = f"{base_url}/v1/models"
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 测试 models 接口...")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            models = result.get("data", [])
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 可用模型 ({len(models)}):")
            for m in models[:10]:
                print(f"  - {m.get('id', 'unknown')}")
            if len(models) > 10:
                print(f"  ... 还有 {len(models) - 10} 个模型")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] models 接口失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {e}")
        return False


def test_health_endpoint(base_url="http://localhost:20128"):
    """测试 /health 接口"""
    url = f"{base_url}/health"
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 测试 health 接口...")

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 健康检查通过")
            try:
                print(f"  {response.json()}")
            except:
                print(f"  {response.text}")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] health 检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {e}")
        return False


if __name__ == "__main__":
    base_url = "http://localhost:20128"

    print("=" * 60)
    print("LLM 服务测试脚本")
    print(f"目标: {base_url}")
    print("=" * 60)

    # 测试健康检查
    test_health_endpoint(base_url)

    # 测试模型列表
    test_models_endpoint(base_url)

    # 测试 chat completions
    print()
    test_llm_service(f"{base_url}/v1/chat/completions")

    print("\n" + "=" * 60)
    print("测试完成")