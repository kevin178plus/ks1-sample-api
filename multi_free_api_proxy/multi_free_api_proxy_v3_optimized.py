"""
多Free API代理服务 - 优化版本
自动检测、测试和轮换使用多个Free API
"""

import os
import sys
import json
import time
import threading
import socket
import requests
import importlib.util
import random
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 导入本地模块
from config import get_config
from app_state import AppState
from errors import ErrorType, APIError, TimeoutError, UpstreamError, ConcurrentLimitError, NoAvailableAPIError

# 初始化配置和状态
config = get_config()
app_state = AppState(config)

# 创建 Flask 应用
app = Flask(__name__, template_folder='templates', static_folder='static')

# 配置 requests 会话
session = requests.Session()

class FileChangeHandler(FileSystemEventHandler):
    """监控文件变化"""
    def on_modified(self, event):
        if not event.is_directory:
            filename = Path(event.src_path).name
            if filename in config.WATCHED_FILES:
                print(f"\n[监控] 检测到文件变化: {filename}")
                print("[监控] 将在下一个请求后重启服务...")
                app_state.restart_flag = True

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def load_env():
    """加载环境变量"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

def load_api_configs():
    """从free_api_test目录自动加载API配置"""
    script_dir = Path(__file__).parent
    free_api_dir = script_dir.parent / "free_api_test"

    print(f"[调试] 脚本目录: {script_dir}")
    print(f"[调试] API目录: {free_api_dir}")

    if not free_api_dir.exists():
        print(f"[警告] 未找到 free_api_test 目录: {free_api_dir}")
        return

    api_dirs = list(free_api_dir.glob("free*"))
    print(f"[调试] 找到 {len(api_dirs)} 个 API 目录: {[d.name for d in api_dirs]}")

    for api_dir in sorted(api_dirs):
        api_name = api_dir.name
        config_file = api_dir / "config.py"

        if not config_file.exists():
            print(f"[跳过] {api_name}: 未找到 config.py")
            continue

        try:
            spec = importlib.util.spec_from_file_location(
                f"config_{api_name}",
                str(config_file)
            )
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)

            api_key = getattr(config_module, "API_KEY", None)
            base_url = getattr(config_module, "BASE_URL", None)
            model_name = getattr(config_module, "MODEL_NAME", None)
            use_proxy = getattr(config_module, "USE_PROXY", False)
            use_sdk = getattr(config_module, "USE_SDK", False)
            available_models = getattr(config_module, "AVAILABLE_MODELS", [])
            max_tokens = getattr(config_module, "MAX_TOKENS", config.DEFAULT_MAX_TOKENS)
            default_weight = getattr(config_module, "DEFAULT_WEIGHT", 10)
            endpoint = getattr(config_module, "ENDPOINT", "/v1/chat/completions")
            response_format = getattr(config_module, "RESPONSE_FORMAT", {
                "content_fields": ["content"],
                "merge_fields": False,
                "use_reasoning_as_fallback": False
            })

            if not base_url or not model_name:
                print(f"[跳过] {api_name}: 配置不完整")
                continue

            env_key = f"{api_name.upper()}_API_KEY"
            env_api_key = os.getenv(env_key)
            if not env_api_key:
                print(f"[跳过] {api_name}: 环境变量 {env_key} 未配置")
                continue

            api_key = env_api_key

            if api_name == "free1":
                use_proxy = True
            elif api_name == "free5":
                use_sdk = True

            api_config = {
                "name": api_name,
                "api_key": api_key,
                "base_url": base_url,
                "model": model_name,
                "available_models": available_models,
                "max_tokens": max_tokens,
                "default_weight": default_weight,
                "use_proxy": use_proxy,
                "endpoint": endpoint,
                "response_format": response_format,
                "available": False,
                "last_test_time": None,
                "last_test_result": None,
                "success_count": 0,
                "failure_count": 0,
                "consecutive_failures": 0
            }

            if use_sdk:
                api_config["use_sdk"] = True

            app_state.add_api(api_name, api_config)
            print(f"[加载] {api_name}: {model_name} @ {base_url}")

        except Exception as e:
            print(f"[错误] 加载 {api_name} 配置失败: {e}")

    print(f"[配置] 已加载 {len(app_state.get_all_apis())} 个API配置")
    init_default_weights()

def init_default_weights():
    """初始化默认权重"""
    weights = {}
    for api_name, api_config in app_state.get_all_apis().items():
        weights[api_name] = api_config.get("default_weight", 10)
    app_state.init_weights(weights)
    print(f"[权重] 默认权重已初始化: {weights}")

def test_api_startup(api_name):
    """启动时测试API是否可用"""
    api_config = app_state.get_api(api_name)
    if not api_config:
        return False

    api_key = api_config["api_key"]
    base_url = api_config["base_url"]
    model = api_config.get("model", "gpt-3.5-turbo")
    use_proxy = api_config.get("use_proxy", False)

    print(f"[启动测试] 测试 {api_name} (模型: {model}, 代理: {use_proxy})...")

    if api_name in ["free5", "free8"]:
        service_port = 5005 if api_name == "free5" else 5008
        service_url = f"http://localhost:{service_port}/health"

        try:
            response = requests.get(service_url, timeout=5)
            if response.status_code == 200:
                api_config["available"] = True
                api_config["last_test_result"] = "success"
                api_config["success_count"] += 1
                print(f"[启动测试] {api_name} 独立服务可用")
                return True
        except Exception as e:
            api_config["available"] = False
            api_config["last_test_result"] = f"error: {str(e)}"
            api_config["failure_count"] += 1
            print(f"[启动测试] {api_name} 独立服务测试失败: {e}")
            return False

    try:
        endpoint = api_config.get("endpoint", "/v1/chat/completions")
        url = f"{base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        proxies = None
        if use_proxy and config.HTTP_PROXY:
            proxies = {
                "http": config.HTTP_PROXY,
                "https": config.HTTP_PROXY
            }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }

        response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=30)

        if response.status_code == 200:
            api_config["available"] = True
            api_config["last_test_result"] = "success"
            api_config["success_count"] += 1
            print(f"[启动测试] {api_name} 可用")
            return True
        else:
            api_config["available"] = False
            api_config["last_test_result"] = f"failed: {response.status_code}"
            api_config["failure_count"] += 1
            print(f"[启动测试] {api_name} 不可用: {response.status_code}")
            return False
    except Exception as e:
        api_config["available"] = False
        api_config["last_test_result"] = f"error: {str(e)}"
        api_config["failure_count"] += 1
        print(f"[启动测试] {api_name} 测试失败: {e}")
        return False

def test_all_apis_startup():
    """启动时测试所有API"""
    print("\n[启动测试] 开始测试所有API...")

    app_state.clear_available_apis()

    for api_name in app_state.get_all_apis():
        api_config = app_state.get_api(api_name)
        if api_config and api_config.get("api_key"):
            if test_api_startup(api_name):
                app_state.add_available_api(api_name)

    available = app_state.get_available_apis()
    print(f"[启动测试] 测试完成，可用API: {len(available)}/{len(app_state.get_all_apis())}")
    if available:
        print(f"[启动测试] 可用API列表: {available}")

def get_next_available_api():
    """获取下一个可用的API（基于权重选择）"""
    available_list = app_state.get_available_apis()
    
    if not available_list:
        return None
    
    # 检查是否有特别权重的API
    special_weight_apis = []
    for api_name in available_list:
        weight = app_state.get_weight(api_name, 10)
        if weight > config.SPECIAL_WEIGHT_THRESHOLD:
            special_weight_apis.append((api_name, weight))
    
    if special_weight_apis:
        special_weight_apis.sort(key=lambda x: x[1], reverse=True)
        selected_api = special_weight_apis[0][0]
        print(f"[权重] 特别权重选中: {selected_api} (权重: {special_weight_apis[0][1]})")
        return selected_api
    
    # 按权重随机选择
    weights = [app_state.get_weight(api_name, 10) for api_name in available_list]
    total_weight = sum(weights)
    
    if total_weight <= 0:
        selected_api = available_list[0]
    else:
        r = random.randint(1, total_weight)
        cumulative = 0
        selected_api = available_list[0]
        for i, api_name in enumerate(available_list):
            cumulative += weights[i]
            if r <= cumulative:
                selected_api = api_name
                break
    
    return selected_api

def mark_api_failure(api_name):
    """标记API失败"""
    api_config = app_state.get_api(api_name)
    if not api_config:
        return
    
    api_config["consecutive_failures"] = api_config.get("consecutive_failures", 0) + 1
    api_config["failure_count"] += 1
    
    consecutive = api_config["consecutive_failures"]
    print(f"[API状态] {api_name} 连续失败次数: {consecutive}/{config.MAX_CONSECUTIVE_FAILURES}")
    
    if consecutive >= config.MAX_CONSECUTIVE_FAILURES:
        app_state.remove_available_api(api_name)
        api_config["available"] = False
        api_config["last_test_result"] = f"marked invalid after {consecutive} consecutive failures"
        print(f"[API状态] {api_name} 已标记为无效")

def mark_api_success(api_name):
    """标记API成功"""
    api_config = app_state.get_api(api_name)
    if not api_config:
        return
    
    api_config["consecutive_failures"] = 0
    api_config["success_count"] += 1
    
    if api_name not in app_state.get_available_apis() and api_config.get("api_key"):
        app_state.add_available_api(api_name)
        api_config["available"] = True
        print(f"[API状态] {api_name} 已恢复并重新加入可用列表")

def decrease_api_weight(api_name):
    """自动减少API权重"""
    current_weight = app_state.get_weight(api_name, 10)
    
    if current_weight > config.SPECIAL_WEIGHT_THRESHOLD:
        if current_weight > config.MIN_AUTO_DECREASE_WEIGHT:
            new_weight = current_weight - 1
            app_state.set_weight(api_name, new_weight)
            print(f"[权重] {api_name} 权重自动减少: {current_weight} -> {new_weight}")

# ==================== 路由定义 ====================

@app.route('/debug', methods=['GET'])
def debug_page():
    """调试页面"""
    if not config.DEBUG_MODE:
        return "Debug mode not enabled", 403
    return render_template('debug.html')

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    # 检查重启标志
    if app_state.restart_flag:
        print("\n[重启] 检测到配置变化，重新加载...")
        try:
            load_env()
            app_state.restart_flag = False
            print("[重启] 重新加载完成")
        except Exception as e:
            print(f"[错误] 重新加载失败: {e}")
            return jsonify({"error": f"Configuration reload failed: {str(e)}"}), 500

    # 并发控制
    max_wait_time = 120
    wait_start = time.time()

    while True:
        if app_state.get_active_requests() < config.MAX_CONCURRENT_REQUESTS:
            app_state.increment_active_requests()
            break

        elapsed = time.time() - wait_start
        if elapsed > max_wait_time:
            print(f"[并发] 等待超时 (已等待 {elapsed:.1f}s)")
            app_state.set_error(ErrorType.CONCURRENT_LIMIT.value, 
                              f"Concurrent limit exceeded: {app_state.get_active_requests()}/{config.MAX_CONCURRENT_REQUESTS}")
            return jsonify({
                "error": "Server too busy - concurrent request limit exceeded",
                "current": app_state.get_active_requests(),
                "limit": config.MAX_CONCURRENT_REQUESTS
            }), 503

        time.sleep(0.1)

    try:
        data = request.get_json()
        message_id = str(time.time())

        print(f"[请求] 收到请求 (ID: {message_id})")

        # 执行请求
        result, retry_count, used_api_name = execute_with_free_api(data, message_id)

        print(f"[请求] 请求成功 (ID: {message_id}, API: {used_api_name}, 重试: {retry_count})")

        return jsonify(result), 200

    except Exception as e:
        print(f"[错误] 请求失败: {str(e)}")
        app_state.set_error(ErrorType.UNKNOWN.value, str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        app_state.decrement_active_requests()
        print(f"[并发] 请求完成 (当前: {app_state.get_active_requests()}/{config.MAX_CONCURRENT_REQUESTS})")

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出所有API支持的模型"""
    models = []
    for api_name, api_config in app_state.get_all_apis().items():
        models.append({
            "id": api_config["model"],
            "object": "model",
            "owned_by": api_name,
            "permission": []
        })

    return jsonify({
        "object": "list",
        "data": models
    })

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

@app.route('/health/upstream', methods=['GET'])
def health_upstream():
    """检查上游 API 连接状态"""
    available = app_state.get_available_apis()
    return jsonify({
        "status": "ok" if available else "degraded",
        "available_apis": available,
        "total_apis": len(app_state.get_all_apis())
    })

@app.route('/debug/stats', methods=['GET'])
def debug_stats():
    """获取调试统计信息"""
    try:
        cache_dir = config.CACHE_DIR
        if not cache_dir:
            return jsonify({
                "total": 0,
                "success": 0,
                "failed": 0,
                "timeout": 0,
                "retry": 0,
                "date": datetime.now().strftime("%Y%m%d"),
                "last_updated": datetime.now().isoformat()
            })

        today = datetime.now().strftime("%Y%m%d")
        counter_file = Path(cache_dir) / f"CALLS_{today}.json"

        if counter_file.exists():
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        else:
            return jsonify({
                "total": 0,
                "success": 0,
                "failed": 0,
                "timeout": 0,
                "retry": 0,
                "date": today,
                "last_updated": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug/apis', methods=['GET'])
def debug_apis():
    """获取所有API的状态"""
    return jsonify({
        "free_apis": app_state.get_all_apis(),
        "available_apis": app_state.get_available_apis()
    })

@app.route('/debug/concurrency', methods=['GET'])
def debug_concurrency():
    """获取并发状态"""
    return jsonify({
        "active_requests": app_state.get_active_requests(),
        "max_concurrent": config.MAX_CONCURRENT_REQUESTS,
        "last_error": app_state.get_error(),
        "call_history": app_state.get_history()
    })

@app.route('/debug/api/enable', methods=['POST'])
def enable_api():
    """启用指定的API"""
    try:
        data = request.get_json()
        api_name = data.get('api_name')

        if not api_name or api_name not in app_state.get_all_apis():
            return jsonify({"success": False, "error": "Invalid API name"}), 400

        api_config = app_state.get_api(api_name)
        if api_config and api_config.get("api_key"):
            app_state.add_available_api(api_name)
            api_config["available"] = True
            return jsonify({"success": True, "message": f"{api_name} enabled"})
        else:
            return jsonify({"success": False, "error": "API key not configured"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug/api/disable', methods=['POST'])
def disable_api():
    """停用指定的API"""
    try:
        data = request.get_json()
        api_name = data.get('api_name')

        if not api_name or api_name not in app_state.get_all_apis():
            return jsonify({"success": False, "error": "Invalid API name"}), 400

        app_state.remove_available_api(api_name)
        api_config = app_state.get_api(api_name)
        if api_config:
            api_config["available"] = False

        return jsonify({"success": True, "message": f"{api_name} disabled"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug/api/weight', methods=['POST'])
def set_api_weight():
    """设置API的权重"""
    try:
        data = request.get_json()
        api_name = data.get('api_name')
        weight = data.get('weight')

        if not api_name or api_name not in app_state.get_all_apis():
            return jsonify({"success": False, "error": "Invalid API name"}), 400

        if not isinstance(weight, int) or weight < 0:
            return jsonify({"success": False, "error": "Weight must be non-negative integer"}), 400

        app_state.set_weight(api_name, weight)
        return jsonify({"success": True, "message": f"Weight set to {weight}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug/api/weight', methods=['GET'])
def get_api_weights():
    """获取所有API的权重配置"""
    try:
        api_details = {}
        for api_name in app_state.get_all_apis():
            api_config = app_state.get_api(api_name)
            api_details[api_name] = {
                "weight": app_state.get_weight(api_name, 10),
                "enabled": api_name in app_state.get_available_apis(),
                "model": api_config.get("model", "unknown") if api_config else "unknown"
            }

        return jsonify({
            "api_weights": app_state.get_all_weights(),
            "api_details": api_details
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug/api/weight/reset', methods=['POST'])
def reset_api_weights():
    """重置所有API权重为默认值"""
    try:
        init_default_weights()
        return jsonify({"success": True, "message": "Weights reset to default"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def execute_with_free_api(data, message_id):
    """使用Free API执行请求"""
    retry_count = 0
    last_error = None
    used_api_name = None

    for attempt in range(config.MAX_RETRIES):
        api_name = get_next_available_api()

        if not api_name:
            raise NoAvailableAPIError("No available Free API")

        api_config = app_state.get_api(api_name)

        try:
            # 简化的请求执行逻辑
            endpoint = api_config.get("endpoint", "/v1/chat/completions")
            url = f"{api_config['base_url']}{endpoint}"
            headers = {
                'Authorization': f'Bearer {api_config["api_key"]}',
                'Content-Type': 'application/json'
            }

            proxies = None
            if api_config.get("use_proxy") and config.HTTP_PROXY:
                proxies = {
                    "http": config.HTTP_PROXY,
                    "https": config.HTTP_PROXY
                }

            current_timeout = config.TIMEOUT_RETRY if attempt > 0 else config.TIMEOUT_BASE
            print(f"[请求] 发送到 {api_name} (尝试 {attempt + 1}/{config.MAX_RETRIES})")

            request_data = {
                "model": api_config.get("model"),
                "messages": data.get("messages", []),
                "temperature": data.get("temperature", config.DEFAULT_TEMPERATURE),
                "max_tokens": data.get("max_tokens", api_config.get("max_tokens", config.DEFAULT_MAX_TOKENS)),
                "top_p": data.get("top_p", config.DEFAULT_TOP_P),
            }

            response = session.post(
                url,
                json=request_data,
                headers=headers,
                proxies=proxies,
                timeout=current_timeout
            )
            response.raise_for_status()

            result = response.json()
            mark_api_success(api_name)
            decrease_api_weight(api_name)
            used_api_name = api_name

            return result, retry_count, used_api_name

        except requests.exceptions.Timeout as e:
            last_error = e
            print(f"[请求] 超时 (尝试 {attempt + 1}/{config.MAX_RETRIES})")
            mark_api_failure(api_name)

            if attempt < config.MAX_RETRIES - 1:
                retry_count += 1
                wait_time = 2 ** attempt
                print(f"[重试] {wait_time}秒后重试...")
                time.sleep(wait_time)

        except requests.exceptions.ConnectionError as e:
            last_error = e
            print(f"[请求] 连接错误 (尝试 {attempt + 1}/{config.MAX_RETRIES})")
            mark_api_failure(api_name)

            if attempt < config.MAX_RETRIES - 1:
                retry_count += 1
                wait_time = 2 ** attempt
                print(f"[重试] {wait_time}秒后重试...")
                time.sleep(wait_time)

        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
            print(f"[请求] HTTP错误 {status_code} (尝试 {attempt + 1}/{config.MAX_RETRIES})")
            mark_api_failure(api_name)

            if 500 <= status_code < 600 and attempt < config.MAX_RETRIES - 1:
                retry_count += 1
                wait_time = 2 ** attempt
                print(f"[重试] {wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                break

        except Exception as e:
            last_error = e
            print(f"[请求] 失败 (尝试 {attempt + 1}/{config.MAX_RETRIES}): {str(e)}")
            mark_api_failure(api_name)
            break

    raise last_error if last_error else NoAvailableAPIError("Request failed")

def start_file_watcher():
    """启动文件监控"""
    observer = Observer()
    observer.schedule(FileChangeHandler(), path='.', recursive=False)
    observer.start()
    return observer

def main():
    """主函数"""
    load_env()
    load_api_configs()
    test_all_apis_startup()

    observer = start_file_watcher()

    if is_port_in_use(config.PORT):
        print(f"[错误] 端口 {config.PORT} 已被占用")
        sys.exit(1)

    print(f"[启动] 多Free API代理服务启动在端口 {config.PORT}")
    print(f"[启动] 可用API: {len(app_state.get_available_apis())}/{len(app_state.get_all_apis())}")

    try:
        app.run(host=config.HOST, port=config.PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[停止] 服务正在停止...")
        observer.stop()
        observer.join()
        print("[停止] 服务已停止")

if __name__ == "__main__":
    main()
