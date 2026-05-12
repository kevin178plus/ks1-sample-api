"""
测试本地 LLM 服务 - 多种模型
"""
import requests
import json
from datetime import datetime


def test_model(model, desc):
    """测试单个模型"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 测试: {desc} ({model})")

    url = "http://localhost:20128/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 50
    }

    try:
        r = requests.post(url, json=payload, timeout=30)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 状态: {r.status_code}")

        if r.status_code == 200:
            result = r.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] {content[:100]}")
            return True
        else:
            try:
                error = r.json()
                msg = error.get("error", {}).get("message", str(error))[:200]
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {msg}")
            except:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {r.text[:200]}")
            return False

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LLM 服务多模型测试")
    print("=" * 60)

    models = [
        ("nvidia/minimaxai/minimax-m2.7", "MiniMax M2.7 (NVIDIA)"),
        ("MiniMax-M2.5", "MiniMax M2.5"),
        ("kr/glm-5", "GLM-5 (KR)"),
        ("kr/deepseek-3.2", "DeepSeek 3.2 (KR)"),
    ]

    results = {}
    for model, desc in models:
        results[desc] = test_model(model, desc)
        print()

    print("=" * 60)
    print("测试结果汇总:")
    print("-" * 40)
    for desc, ok in results.items():
        status = "[OK]" if ok else "[FAIL]"
        print(f"  {status} {desc}")

    success_count = sum(1 for v in results.values() if v)
    print(f"\n成功率: {success_count}/{len(results)}")
