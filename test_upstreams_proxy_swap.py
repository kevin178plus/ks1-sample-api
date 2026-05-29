"""
上游连接测试脚本
测试所有上游的连接状态，对失败的上游尝试反转 use_proxy 参数再测试
"""

import os
import sys
import yaml
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置
UPSTREAMS_DIR = Path(__file__).parent / "api-proxy-go" / "upstreams"
TIMEOUT = 15  # 超时时间（秒）
TEST_MODEL = "gpt-3.5-turbo"
TEST_PROMPT = "Hello, are you there?"

# 当前系统代理（如果有）
SYSTEM_HTTP_PROXY = os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or ""


def load_upstream_config(upstream_dir: Path) -> dict:
    """加载上游配置文件"""
    config_path = upstream_dir / "config.yaml"
    if not config_path.exists():
        return None
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_upstream_connection(config: dict, test_proxy: bool = None) -> dict:
    """
    测试上游连接
    test_proxy: None=使用原配置, True=强制用代理, False=强制不用代理
    """
    name = config.get("name", "unknown")
    address = config.get("address", "")
    original_use_proxy = config.get("use_proxy", False)
    
    # 确定本次测试的 use_proxy 值
    if test_proxy is not None:
        use_proxy = test_proxy
    else:
        use_proxy = original_use_proxy
    
    # 准备请求配置
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "API-Proxy-Test/1.0",
    }
    
    # 构建请求体（适配不同 API 格式）
    if "openrouter" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        # OpenRouter 特殊处理
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    elif "chatanywhere" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    elif "groq" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    elif "cerebras" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    elif "generativelanguage.googleapis.com" in address:
        # Gemini API 格式不同
        body = {
            "contents": [{"parts": [{"text": TEST_PROMPT}]}],
            "generationConfig": {"maxOutputTokens": 100},
        }
        # Gemini 不需要 Authorization header，但需要 API key in URL
    elif "cohere" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    elif "sambanova" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    elif "freemodel" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    elif "sensenova" in address.lower():
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    else:
        # 通用 OpenAI 格式
        body = {
            "model": config.get("model", TEST_MODEL),
            "messages": [{"role": "user", "content": TEST_PROMPT}],
            "max_tokens": 100,
        }
        if not config.get("api_key"):
            headers["Authorization"] = "Bearer dummy"
    
    # 准备代理设置
    proxies = None
    if use_proxy and SYSTEM_HTTP_PROXY:
        proxies = {"http": SYSTEM_HTTP_PROXY, "https": SYSTEM_HTTP_PROXY}
    elif use_proxy and not SYSTEM_HTTP_PROXY:
        # 没有系统代理但要求用代理，跳过
        return {
            "name": name,
            "address": address,
            "use_proxy": use_proxy,
            "success": False,
            "error": "需要代理但无系统代理配置",
            "swapped": test_proxy is not None,
        }
    
    # 发送请求
    try:
        # Gemini 特殊处理（API key 在 URL 中）
        if "generativelanguage.googleapis.com" in address:
            test_url = f"{address}/models/gemini-2.0-flash:generateContent"
            resp = requests.post(
                test_url,
                headers=headers,
                json=body,
                timeout=TIMEOUT,
                proxies=proxies,
            )
        else:
            # 通用格式：POST /v1/chat/completions
            test_url = f"{address.rstrip('/')}/v1/chat/completions"
            resp = requests.post(
                test_url,
                headers=headers,
                json=body,
                timeout=TIMEOUT,
                proxies=proxies,
            )
        
        # 判断结果
        if resp.status_code == 200:
            return {
                "name": name,
                "address": address,
                "use_proxy": use_proxy,
                "success": True,
                "status_code": resp.status_code,
                "swapped": test_proxy is not None,
            }
        elif resp.status_code == 401:
            # 401 表示连接成功但 API key 无效（这是正常的，因为没配 key）
            return {
                "name": name,
                "address": address,
                "use_proxy": use_proxy,
                "success": True,
                "status_code": resp.status_code,
                "note": "连接成功（401=API key 缺失/无效，属正常）",
                "swapped": test_proxy is not None,
            }
        elif resp.status_code == 404:
            # 404 可能表示 endpoint 不对，但仍算连接成功
            return {
                "name": name,
                "address": address,
                "use_proxy": use_proxy,
                "success": True,
                "status_code": resp.status_code,
                "note": "连接成功（404=endpoint 可能不匹配）",
                "swapped": test_proxy is not None,
            }
        else:
            return {
                "name": name,
                "address": address,
                "use_proxy": use_proxy,
                "success": False,
                "status_code": resp.status_code,
                "error": f"HTTP {resp.status_code}",
                "swapped": test_proxy is not None,
            }
            
    except requests.exceptions.Timeout:
        return {
            "name": name,
            "address": address,
            "use_proxy": use_proxy,
            "success": False,
            "error": "超时",
            "swapped": test_proxy is not None,
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "name": name,
            "address": address,
            "use_proxy": use_proxy,
            "success": False,
            "error": f"连接错误: {str(e)[:100]}",
            "swapped": test_proxy is not None,
        }
    except Exception as e:
        return {
            "name": name,
            "address": address,
            "use_proxy": use_proxy,
            "success": False,
            "error": f"异常: {str(e)[:100]}",
            "swapped": test_proxy is not None,
        }


def get_all_upstreams() -> list:
    """获取所有上游配置"""
    upstreams = []
    for item in sorted(UPSTREAMS_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith("_"):
            config = load_upstream_config(item)
            if config and config.get("enabled", True):
                upstreams.append(config)
    return upstreams


def main():
    print("=" * 70)
    print("🔍 上游连接测试")
    print("=" * 70)
    print(f"系统代理: {SYSTEM_HTTP_PROXY or '(未配置)'}")
    print(f"超时时间: {TIMEOUT}秒")
    print()
    
    upstreams = get_all_upstreams()
    print(f"共发现 {len(upstreams)} 个启用的上游")
    print()
    
    results = []
    swapped_results = []
    
    # 第一阶段：用原配置测试所有上游
    print("📋 第一阶段：使用原配置测试所有上游")
    print("-" * 70)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_config = {
            executor.submit(test_upstream_connection, cfg): cfg 
            for cfg in upstreams
        }
        for future in as_completed(future_to_config):
            result = future.result()
            results.append(result)
            cfg = future_to_config[future]
            status = "✅ 成功" if result["success"] else "❌ 失败"
            swap_note = " [已反转use_proxy]" if result.get("swapped") else ""
            print(f"  {cfg['name']:>8} | use_proxy={str(cfg.get('use_proxy', False)):>5} | {status}{swap_note}")
            if result.get("error"):
                print(f"           → {result['error']}")
    
    # 统计失败的
    failed = [r for r in results if not r["success"]]
    if not failed:
        print("\n🎉 所有上游连接成功！无需反转 use_proxy。")
        return
    
    print(f"\n⚠️  {len(failed)} 个上游连接失败，尝试反转 use_proxy 参数再测试...")
    print()
    
    # 第二阶段：对失败的 upstream 反转 use_proxy 再测试
    print("🔄 第二阶段：反转 use_proxy 参数重试")
    print("-" * 70)
    
    # 找出失败的 upstream 配置
    failed_configs = {}
    for r in failed:
        for cfg in upstreams:
            if cfg["name"] == r["name"]:
                failed_configs[cfg["name"]] = cfg
                break
    
    # 重新打开 executor 进行第二阶段测试
    futures = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for name, cfg in failed_configs.items():
            original_proxy = cfg.get("use_proxy", False)
            new_proxy = not original_proxy
            future = executor.submit(test_upstream_connection, cfg, test_proxy=new_proxy)
            futures[future] = (name, cfg, original_proxy, new_proxy)
        
        for future in as_completed(futures):
            name, cfg, orig, new = futures[future]
            result = future.result()
            swapped_results.append(result)
            status = "✅ 成功（反转后）" if result["success"] else "❌ 仍失败"
            print(f"  {name:>8} | use_proxy: {str(orig):>5} → {str(new):>5} | {status}")
            if result.get("error"):
                print(f"           → {result['error']}")
    
    # 汇总报告
    print()
    print("=" * 70)
    print("📊 测试汇总报告")
    print("=" * 70)
    
    success_original = [r for r in results if r["success"]]
    success_swapped = [r for r in swapped_results if r["success"]]
    still_failed = [r for r in swapped_results if not r["success"]]
    
    print(f"\n  原始配置成功: {len(success_original)} 个")
    print(f"  反转后成功:   {len(success_swapped)} 个")
    print(f"  仍失败:       {len(still_failed)} 个")
    
    if success_swapped:
        print(f"\n🔧 以下上游反转 use_proxy 后恢复：")
        for r in success_swapped:
            cfg = next((c for c in upstreams if c["name"] == r["name"]), None)
            if cfg:
                orig = cfg.get("use_proxy", False)
                print(f"   • {r['name']}: use_proxy {str(orig)} → {str(not orig)}")
    
    if still_failed:
        print(f"\n⚠️  以下上游即使反转 use_proxy 仍无法连接：")
        for r in still_failed:
            print(f"   • {r['name']}: {r.get('error', '未知错误')}")
    
    # 生成建议修改的配置文件列表
    if success_swapped:
        print(f"\n📝 建议修改以下上游的 config.yaml（反转 use_proxy）：")
        for r in success_swapped:
            cfg = next((c for c in upstreams if c["name"] == r["name"]), None)
            if cfg:
                config_file = UPSTREAMS_DIR / r["name"] / "config.yaml"
                orig = cfg.get("use_proxy", False)
                new = not orig
                print(f"   • {config_file.relative_to(UPSTREAMS_DIR.parent.parent)}: use_proxy: {str(orig)} → {str(new)}")
    
    print()


if __name__ == "__main__":
    main()
