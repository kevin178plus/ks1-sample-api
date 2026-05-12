"""
测试本地 LLM 服务 - SSE 流式响应处理
"""
import requests
import json
from datetime import datetime


API_KEY = "sk-04d6316e048123a3-sjc5o8-39270609"
BASE_URL = "http://localhost:20128"


def parse_sse(text):
    """解析 SSE 格式响应"""
    lines = text.strip().split("\n")
    for line in lines:
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                return None
            try:
                return json.loads(data)
            except:
                continue
    return None


def test_stream(model, use_stream=False):
    """测试模型（支持流式）"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 测试: {model} (stream={use_stream})")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply OK only"}],
        "max_tokens": 50,
        "stream": use_stream
    }

    try:
        start = datetime.now()
        r = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload, headers=headers, timeout=30)
        elapsed = (datetime.now() - start).total_seconds()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 状态: {r.status_code} ({elapsed:.2f}s)")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Content-Type: {r.headers.get('Content-Type', 'N/A')}")

        if r.status_code == 200:
            content_type = r.headers.get("Content-Type", "")

            if "text/event-stream" in content_type or "stream" in content_type.lower():
                # SSE 流式响应
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 检测到 SSE 流式响应")

                full_content = ""
                chunks = 0
                for line in r.text.strip().split("\n"):
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            chunks += 1
                            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            full_content += delta
                        except:
                            continue

                print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 流式响应 ({chunks} chunks)")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 内容: {full_content[:200]}")
                return True

            else:
                # 普通 JSON 响应
                try:
                    result = r.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] {content[:200]}")
                    return True
                except:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [FAIL] 响应格式异常: {r.text[:200]}")
                    return False
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
    print("LLM 服务测试 (SSE 流式支持)")
    print("=" * 60)

    models = [
        ("nvidia/minimaxai/minimax-m2.7", True),
        ("kr/glm-5", True),
        ("MiniMax-M2.5", True),
        ("kr/deepseek-3.2", True),
    ]

    results = {}
    for model, use_stream in models:
        results[model] = test_stream(model, use_stream)
        print()

    print("=" * 60)
    print("结果汇总:")
    print("-" * 40)
    for model, ok in results.items():
        print(f"  {'[OK]' if ok else '[FAIL]'} {model}")

    success = sum(1 for v in results.values() if v)
    print(f"\n成功率: {success}/{len(results)}")
