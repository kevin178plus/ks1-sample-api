"""
测试本地 LLM 服务 - 使用 API Key
"""
import requests
import json
from datetime import datetime


API_KEY = "sk-04d6316e048123a3-sjc5o8-39270609"
BASE_URL = "http://localhost:20128"


def test_models():
    """获取可用模型列表"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取模型列表...")

    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        r = requests.get(f"{BASE_URL}/v1/models", headers=headers, timeout=10)
        if r.status_code == 200:
            result = r.json()
            models = result.get("data", [])
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 可用模型 ({len(models)}):")
            for m in models[:10]:
                print(f"  - {m.get('id', 'unknown')}")
            return models
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {r.status_code}: {r.text[:200]}")
            return []
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {e}")
        return []


def test_chat(model):
    """测试聊天接口"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 测试聊天: {model}")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "你好，回复 OK 即可"}],
        "max_tokens": 100,
        "temperature": 0.1
    }

    try:
        start = datetime.now()
        r = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, headers=headers, timeout=60)
        elapsed = (datetime.now() - start).total_seconds()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 状态: {r.status_code} ({elapsed:.2f}s)")

        if r.status_code == 200:
            result = r.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 回复: {content[:200]}")
            if "usage" in result:
                u = result["usage"]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Usage: {u}")
            return True
        else:
            try:
                error = r.json()
                msg = error.get("error", {}).get("message", str(error))[:300]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {msg}")
            except:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {r.text[:300]}")
            return False

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LLM 服务测试 (使用 API Key)")
    print(f"URL: {BASE_URL}")
    print("=" * 60)

    # 获取模型列表
    models = test_models()

    # 测试几个模型
    test_list = [
        "MiniMax-M2.5",
        "nvidia/minimaxai/minimax-m2.7",
        "kr/glm-5",
        "kr/deepseek-3.2",
    ]

    print("\n" + "=" * 60)
    print("测试聊天接口:")
    print("=" * 60)

    results = {}
    for model in test_list:
        results[model] = test_chat(model)

    print("\n" + "=" * 60)
    print("结果汇总:")
    print("-" * 40)
    for model, ok in results.items():
        print(f"  {'[OK]' if ok else '[FAIL]'} {model}")

    success = sum(1 for v in results.values() if v)
    print(f"\n成功率: {success}/{len(results)}")
