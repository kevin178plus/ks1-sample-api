#!/usr/bin/env python3
"""
多角度 API 测试脚本
测试 free13 在不同网络配置下的表现：
1. 不使用代理（直连）
2. 使用本地代理（127.0.0.1:7897）
3. 不同的超时时间
4. 不同的请求参数
"""

import requests
import json
import sys
import time
from pathlib import Path
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
    MAX_TOKENS = getattr(config_module, 'MAX_TOKENS', 5000)
else:
    print("[错误] 未找到 config.py 文件")
    sys.exit(1)

# 验证 API Key
if not API_KEY:
    api_key_env = f"FREE{script_dir.name.replace('free', '')}_API_KEY"
    raise ValueError(f"{api_key_env} 未在 .env 文件中配置")

# 读取提示词
ask_file = script_dir / 'ask.txt'
try:
    with open(ask_file, 'r', encoding='utf-8') as f:
        PROMPT = f.read()
except Exception as e:
    print(f"[警告] 无法读取 ask.txt: {e}")
    PROMPT = "Hello, please introduce yourself."


def format_time(seconds):
    """格式化时间为秒和毫秒"""
    return f"{seconds:.2f}s"


def test_connection(proxy_url=None, timeout=30, description=""):
    """测试基础连接"""
    print(f"\n{'='*60}")
    print(f"测试：{description}")
    print(f"代理：{proxy_url if proxy_url else '直连'}")
    print(f"超时：{timeout}秒")
    print(f"{'='*60}")
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    } if proxy_url else None
    
    results = {}
    
    # 测试 1: 简单的 GET 请求（健康检查）
    print("\n[测试 1] 基础连接测试 (GET /)")
    try:
        start_time = time.time()
        response = requests.get(
            BASE_URL.replace('/v1', ''),
            headers={'Authorization': f'Bearer {API_KEY}'},
            proxies=proxies,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        
        results['base_connection'] = {
            'status': response.status_code,
            'time': elapsed,
            'success': response.status_code < 500
        }
        
        print(f"状态码：{response.status_code}")
        print(f"响应时间：{format_time(elapsed)}")
        print(f"结果：{'[OK] 成功' if response.status_code < 500 else '[FAIL] 失败'}")
    except requests.Timeout:
        results['base_connection'] = {'status': 'TIMEOUT', 'time': timeout, 'success': False}
        print(f"[TIMEOUT] 请求超时 ({timeout}秒)")
    except requests.ConnectionError as e:
        results['base_connection'] = {'status': 'CONNECTION_ERROR', 'error': str(e), 'success': False}
        print(f"[CONNECTION ERROR] 连接错误：{e}")
    except Exception as e:
        results['base_connection'] = {'status': 'ERROR', 'error': str(e), 'success': False}
        print(f"[ERROR] 未知错误：{e}")
    
    # 测试 2: Models 端点（如果支持）
    print("\n[测试 2] Models 端点测试 (GET /models)")
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/models",
            headers={'Authorization': f'Bearer {API_KEY}'},
            proxies=proxies,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        
        results['models_endpoint'] = {
            'status': response.status_code,
            'time': elapsed,
            'success': response.status_code == 200
        }
        
        print(f"状态码：{response.status_code}")
        print(f"响应时间：{format_time(elapsed)}")
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            print(f"[OK] 成功！找到 {len(models)} 个模型")
        elif response.status_code == 404:
            print(f"[WARN] 端点不支持 (404)")
        else:
            print(f"[FAIL] 失败：{response.text[:200]}")
    except requests.Timeout:
        results['models_endpoint'] = {'status': 'TIMEOUT', 'success': False}
        print(f"[TIMEOUT] 请求超时 ({timeout}秒)")
    except Exception as e:
        results['models_endpoint'] = {'status': 'ERROR', 'error': str(e), 'success': False}
        print(f"[ERROR] 错误：{e}")
    
    # 测试 3: Chat Completions 端点
    print("\n[测试 3] 聊天完成端点测试 (POST /chat/completions)")
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0.7,
        "max_tokens": min(MAX_TOKENS, 1000)
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            },
            json=payload,
            proxies=proxies,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        
        results['chat_completion'] = {
            'status': response.status_code,
            'time': elapsed,
            'success': response.status_code == 200,
            'response_size': len(response.content)
        }
        
        print(f"状态码：{response.status_code}")
        print(f"响应时间：{format_time(elapsed)}")
        print(f"响应大小：{len(response.content)} bytes")
        
        if response.status_code == 200:
            data = response.json()
            choice = data.get('choices', [{}])[0]
            message = choice.get('message', {})
            content = message.get('content', message.get('reasoning_content', str(message)))
            
            usage = data.get('usage', {})
            print(f"[OK] 成功!")
            print(f"输入 Token: {usage.get('prompt_tokens', 'N/A')}")
            print(f"输出 Token: {usage.get('completion_tokens', 'N/A')}")
            print(f"总 Token: {usage.get('total_tokens', 'N/A')}")
            print(f"回复预览：{content[:100]}...")
        else:
            print(f"[FAIL] 失败：{response.text[:300]}")
    except requests.Timeout:
        results['chat_completion'] = {'status': 'TIMEOUT', 'success': False}
        print(f"[TIMEOUT] 请求超时 ({timeout}秒)")
    except Exception as e:
        results['chat_completion'] = {'status': 'ERROR', 'error': str(e), 'success': False}
        print(f"[ERROR] 错误：{e}")
    
    return results


def run_all_tests():
    """运行所有测试场景"""
    print("=" * 60)
    print("多角度 API 测试 - free13")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:] if len(API_KEY) > 10 else API_KEY}")
    print(f"提示词长度：{len(PROMPT)} 字符")
    
    all_results = []
    
    # 场景 1: 直连 + 标准超时 (30 秒)
    print("\n>>> 开始场景 1/6: 直连 - 标准超时")
    result1 = test_connection(
        proxy_url=None,
        timeout=30,
        description="直连 - 标准超时 (30 秒)"
    )
    all_results.append(("直连 -30s", result1))
    
    # 场景 2: 直连 + 长超时 (60 秒)
    print("\n>>> 开始场景 2/6: 直连 - 长超时")
    result2 = test_connection(
        proxy_url=None,
        timeout=60,
        description="直连 - 长超时 (60 秒)"
    )
    all_results.append(("直连 -60s", result2))
    
    # 场景 3: 直连 + 超长超时 (120 秒) - 可选，如果前两个都失败则跳过
    print("\n>>> 是否执行场景 3/6: 直连 - 超长超时 (120 秒)?")
    print("提示：此测试可能需要等待较长时间")
    # 如果前两次聊天完成都失败（超时），询问是否继续
    chat_failures = sum(1 for _, r in all_results if not r.get('chat_completion', {}).get('success'))
    if chat_failures == 2:
        print(f"[WARN] 前 2 次聊天完成测试均失败（超时）")
        print("建议：直接跳过 120 秒测试，进入代理测试")
        skip_long_timeout = True
    else:
        skip_long_timeout = False
    
    if not skip_long_timeout:
        result3 = test_connection(
            proxy_url=None,
            timeout=120,
            description="直连 - 超长超时 (120 秒)"
        )
        all_results.append(("直连 -120s", result3))
    else:
        print("[跳过] 直连 -120s 测试")
        all_results.append(("直连 -120s", {'skipped': True}))
    
    # 场景 4: 使用代理 + 标准超时
    print("\n>>> 开始场景 4/6: 代理 - 标准超时")
    print("提示：如果代理不可用，将快速失败并继续下一个测试")
    try:
        # 先测试代理是否可用
        proxy_test = requests.get(
            "http://www.google.com",
            proxies={'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'},
            timeout=5
        )
        print("[OK] 代理服务器可用")
        
        result4 = test_connection(
            proxy_url="http://127.0.0.1:7897",
            timeout=30,
            description="代理 (127.0.0.1:7897) - 标准超时 (30 秒)"
        )
        all_results.append(("代理 -30s", result4))
    except Exception as e:
        print(f"[WARN] 代理服务器不可用：{e}")
        print("[跳过] 后续代理测试")
        all_results.append(("代理 -30s", {'skipped': True, 'reason': str(e)}))
        all_results.append(("代理 -60s", {'skipped': True}))
        all_results.append(("代理 -120s", {'skipped': True}))
        # 打印总结
        return _print_summary(all_results)
    
    # 场景 5: 使用代理 + 长超时
    print("\n>>> 开始场景 5/6: 代理 - 长超时")
    result5 = test_connection(
        proxy_url="http://127.0.0.1:7897",
        timeout=60,
        description="代理 (127.0.0.1:7897) - 长超时 (60 秒)"
    )
    all_results.append(("代理 -60s", result5))
    
    # 场景 6: 使用代理 + 超长超时
    print("\n>>> 开始场景 6/6: 代理 - 超长超时")
    result6 = test_connection(
        proxy_url="http://127.0.0.1:7897",
        timeout=120,
        description="代理 (127.0.0.1:7897) - 超长超时 (120 秒)"
    )
    all_results.append(("代理 -120s", result6))
    
    # 打印总结报告
    return _print_summary(all_results)


def _print_summary(all_results):
    """打印总结报告"""
    print("\n\n" + "=" * 80)
    print("测试结果总结报告")
    print("=" * 80)
    
    for name, results in all_results:
        if results.get('skipped'):
            print(f"\n{name}: [跳过] {results.get('reason', '')}")
            continue
            
        base_status = "[OK]" if results.get('base_connection', {}).get('success') else "[FAIL]"
        models_status = "[OK]" if results.get('models_endpoint', {}).get('success') else ("[WARN]" if results.get('models_endpoint', {}).get('status') == 404 else "[FAIL]")
        chat_status = "[OK]" if results.get('chat_completion', {}).get('success') else "[FAIL]"
        
        print(f"\n{name}:")
        base_time = results.get('base_connection', {}).get('time', 0)
        chat_time = results.get('chat_completion', {}).get('time', 0)
        print(f"  基础连接：{base_status} {results.get('base_connection', {}).get('status', 'N/A')} ({base_time:.2f}s)" if base_time else f"  基础连接：{base_status} {results.get('base_connection', {}).get('status', 'N/A')}")
        print(f"  Models 端点：{models_status} {results.get('models_endpoint', {}).get('status', 'N/A')}")
        print(f"  聊天完成：{chat_status} {results.get('chat_completion', {}).get('status', 'N/A')} ({chat_time:.2f}s)" if chat_time else f"  聊天完成：{chat_status} {results.get('chat_completion', {}).get('status', 'N/A')}")
    
    # 最佳方案推荐
    print("\n\n" + "=" * 80)
    print("推荐配置")
    print("=" * 80)
    
    successful_results = [(n, r) for n, r in all_results if r.get('chat_completion', {}).get('success')]
    if successful_results:
        best_chat_result = max(successful_results, key=lambda x: x[1].get('chat_completion', {}).get('time', 0))
        print(f"\n最佳聊天完成：{best_chat_result[0]} ({best_chat_result[1].get('chat_completion', {}).get('time', 0):.2f}s)")
    else:
        print("\n[WARN] 所有聊天完成测试均失败")
    
    # 统计成功率
    success_count = sum(1 for _, r in all_results if r.get('chat_completion', {}).get('success') and not r.get('skipped'))
    total_count = sum(1 for _, r in all_results if not r.get('skipped'))
    
    success_rate = None
    if total_count > 0:
        success_rate = success_count / total_count * 100
        print(f"\n总成功率：{success_count}/{total_count} ({success_rate:.1f}%)")
    else:
        print(f"\n总成功率：N/A (所有测试均被跳过)")
    
    # 保存详细结果
    report_file = script_dir / 'multi_angle_test_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'base_url': BASE_URL,
                'model': MODEL_NAME,
                'proxy_tested': '127.0.0.1:7897'
            },
            'results': {k: v for k, v in all_results},
            'summary': {
                'total_tests': len(all_results),
                'successful_tests': success_count,
                'skipped_tests': sum(1 for _, r in all_results if r.get('skipped')),
                'success_rate': f"{success_rate:.1f}%" if success_rate is not None else "N/A"
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细报告已保存到：{report_file}")
    
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
