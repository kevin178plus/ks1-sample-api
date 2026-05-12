"""
测试本地 LLM 服务 - 详细响应检查
"""
import requests
from datetime import datetime


API_KEY = "sk-04d6316e048123a3-sjc5o8-39270609"
BASE_URL = "http://localhost:20128"


def test_model_raw(model):
    """测试模型并显示原始响应"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 测试: {model}")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 20
    }

    try:
        start = datetime.now()
        r = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, headers=headers, timeout=30)
        elapsed = (datetime.now() - start).total_seconds()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 状态: {r.status_code} ({elapsed:.2f}s)")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Content-Type: {r.headers.get('Content-Type', 'N/A')}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 响应长度: {len(r.content)} bytes")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 原始响应 (前500字符):")
        print("-" * 40)
        print(r.text[:500])
        print("-" * 40)

        # 尝试解析 JSON
        try:
            result = r.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] {content[:200]}")
            return True
        except:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] 不是有效 JSON")
            return False

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LLM 服务详细测试")
    print("=" * 60)

    models = [
        "nvidia/minimaxai/minimax-m2.7",
        "kr/glm-5",
        "MiniMax-M2.5",
        "kr/deepseek-3.2",
    ]

    for model in models:
        test_model_raw(model)
        print()
