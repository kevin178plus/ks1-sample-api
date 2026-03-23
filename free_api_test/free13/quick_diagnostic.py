#!/usr/bin/env python3
"""
快速诊断测试脚本
专注于测试 free13 的关键问题
"""

import requests
import json
import time
from pathlib import Path
import sys
from dotenv import load_dotenv
import os

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
else:
    print("[错误] 未找到 config.py 文件")
    sys.exit(1)

print("=" * 70)
print("free13 快速诊断测试")
print("=" * 70)
print(f"Base URL: {BASE_URL}")
print(f"Model: {MODEL_NAME}")
print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:] if len(API_KEY) > 10 else API_KEY}\n")

results = {}

# 测试 1: 基础连接（健康检查）
print("[测试 1] 基础连接测试")
print("-" * 70)
try:
    start = time.time()
    resp = requests.get(BASE_URL.replace('/v1', ''), timeout=10)
    elapsed = time.time() - start
    print(f"状态码：{resp.status_code}")
    print(f"响应时间：{elapsed:.2f}s")
    print(f"结果：{'[PASS]' if resp.status_code == 200 else '[FAIL]'}\n")
    results['base'] = {'status': resp.status_code, 'time': elapsed, 'pass': resp.status_code == 200}
except Exception as e:
    print(f"错误：{e}\n")
    results['base'] = {'error': str(e), 'pass': False}

# 测试 2: 直连 - 聊天完成（短超时）
print("[测试 2] 直连 - 聊天完成 (timeout=30s)")
print("-" * 70)
payload = {
    "model": MODEL_NAME,
    "messages": [{"role": "user", "content": "你好"}],
    "temperature": 0.7,
    "max_tokens": 500
}
try:
    start = time.time()
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
        json=payload,
        timeout=30
    )
    elapsed = time.time() - start
    print(f"状态码：{resp.status_code}")
    print(f"响应时间：{elapsed:.2f}s")
    if resp.status_code == 200:
        data = resp.json()
        usage = data.get('usage', {})
        print(f"[PASS] 成功!")
        print(f"总 Token: {usage.get('total_tokens', 'N/A')}")
    else:
        print(f"[FAIL] 失败：{resp.text[:200]}")
    results['direct_30s'] = {'status': resp.status_code, 'time': elapsed, 'pass': resp.status_code == 200}
except requests.Timeout:
    print(f"[TIMEOUT] 请求超时 (30 秒)")
    results['direct_30s'] = {'status': 'TIMEOUT', 'pass': False}
except Exception as e:
    print(f"[ERROR] {e}")
    results['direct_30s'] = {'error': str(e), 'pass': False}

print()

# 测试 3: 代理 - 聊天完成（短超时）
print("[测试 3] 代理 (127.0.0.1:7897) - 聊天完成 (timeout=30s)")
print("-" * 70)
proxies = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
try:
    # 先检查代理是否可用
    print("检查代理服务器...")
    proxy_check = requests.get("http://www.google.com", proxies=proxies, timeout=5)
    print("[OK] 代理服务器可用\n")
    
    start = time.time()
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'},
        json=payload,
        proxies=proxies,
        timeout=30
    )
    elapsed = time.time() - start
    print(f"状态码：{resp.status_code}")
    print(f"响应时间：{elapsed:.2f}s")
    if resp.status_code == 200:
        data = resp.json()
        usage = data.get('usage', {})
        print(f"[PASS] 成功!")
        print(f"总 Token: {usage.get('total_tokens', 'N/A')}")
    else:
        print(f"[FAIL] 失败：{resp.text[:200]}")
    results['proxy_30s'] = {'status': resp.status_code, 'time': elapsed, 'pass': resp.status_code == 200}
except requests.exceptions.ProxyError as e:
    print(f"[PROXY ERROR] 代理不可用：{e}")
    print("[SKIP] 跳过代理测试")
    results['proxy_30s'] = {'error': 'ProxyError', 'pass': False}
except requests.Timeout:
    print(f"[TIMEOUT] 请求超时 (30 秒)")
    results['proxy_30s'] = {'status': 'TIMEOUT', 'pass': False}
except Exception as e:
    print(f"[ERROR] {e}")
    results['proxy_30s'] = {'error': str(e), 'pass': False}

print()

# 总结
print("=" * 70)
print("测试总结")
print("=" * 70)

test_names = {
    'base': '基础连接',
    'direct_30s': '直连 -30s',
    'proxy_30s': '代理 -30s'
}

for key, name in test_names.items():
    result = results.get(key, {})
    if result.get('pass'):
        status = "[PASS]"
    elif result.get('error') or result.get('status') == 'TIMEOUT':
        status = f"[FAIL] {result.get('status', result.get('error', 'Unknown'))}"
    else:
        status = "[FAIL]"
    
    time_str = f" ({result.get('time', 'N/A'):.2f}s)" if isinstance(result.get('time'), float) else ""
    print(f"{name}: {status}{time_str}")

# 建议
print("\n" + "=" * 70)
print("诊断建议")
print("=" * 70)

if not results.get('base', {}).get('pass'):
    print("1. 基础连接失败 - 检查网络连接和 BASE_URL 是否正确")
elif not results.get('direct_30s', {}).get('pass'):
    if results['direct_30s'].get('status') == 'TIMEOUT':
        print("1. 直连超时 - 服务端响应慢，建议:")
        print("   - 增加超时时间到 60-120 秒")
        print("   - 检查 API Key 是否有效/限额")
        print("   - 尝试使用代理服务器")
    else:
        print(f"1. 直连失败 - 状态码：{results['direct_30s'].get('status')}")
        print("   检查 API Key 和模型名称是否正确")

if results.get('proxy_30s', {}).get('pass'):
    print("2. 代理测试通过 - 建议使用代理以获得更好性能")
elif 'proxy_30s' in results and not results['proxy_30s'].get('pass'):
    if results['proxy_30s'].get('error') == 'ProxyError':
        print("2. 代理不可用 - 请检查 127.0.0.1:7897 是否运行")
    elif results['proxy_30s'].get('status') == 'TIMEOUT':
        print("2. 代理超时 - 代理服务器响应慢，建议更换代理或直连")

# 保存结果
report_file = script_dir / 'quick_diagnostic_report.json'
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f"\n详细报告已保存到：{report_file}")
print("=" * 70)

sys.exit(0 if any(r.get('pass') for r in results.values()) else 1)
