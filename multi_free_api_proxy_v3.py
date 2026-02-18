"""
多Free API代理服务
自动检测、测试和轮换使用多个Free API
"""

import os
import json
import sys
import time
import uuid
import threading
import socket
import requests
import re
import subprocess
from pathlib import Path
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# 配置 requests 会话，使用连接池和重试策略
session = requests.Session()

# 全局变量
RESTART_FLAG = False
WATCHED_FILES = {'.env', 'multi_free_api_proxy_v3.py'}
DEBUG_MODE = False
CACHE_DIR = None
HTTP_PROXY = None

# 并发控制相关
MAX_CONCURRENT_REQUESTS = 5
ACTIVE_REQUESTS = 0
REQUEST_QUEUE = deque()
QUEUE_LOCK = threading.Lock()
ACTIVE_LOCK = threading.Lock()

# Free API相关
FREE_APIS = {}
AVAILABLE_APIS = deque()
API_LOCK = threading.Lock()
API_TEST_INTERVAL = 300

# 调用历史记录
CALL_HISTORY = deque(maxlen=10)
HISTORY_LOCK = threading.Lock()

# 错误类型
ERROR_TYPES = {
    "NONE": "none",
    "TIMEOUT": "timeout",
    "UPSTREAM_UNREACHABLE": "upstream_unreachable",
    "API_ERROR": "api_error",
    "CONCURRENT_LIMIT": "concurrent_limit",
    "PROXY_ERROR": "proxy_error",
    "UNKNOWN": "unknown"
}

LAST_ERROR = {"type": ERROR_TYPES["NONE"], "message": "", "timestamp": None}
LAST_ERROR_LOCK = threading.Lock()

class FileChangeHandler(FileSystemEventHandler):
    """监控文件变化"""
    def on_modified(self, event):
        global RESTART_FLAG
        if not event.is_directory:
            filename = Path(event.src_path).name
            if filename in WATCHED_FILES:
                print(f"\n[监控] 检测到文件变化: {filename}")
                print("[监控] 将在下一个请求后重启服务...")
                RESTART_FLAG = True

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def check_debug_mode():
    """检查是否启用调试模式"""
    return Path('DEBUG_MODE.txt').exists()

def save_message_cache(message_type, message_id, data):
    """保存消息到缓存目录"""
    if not DEBUG_MODE or not CACHE_DIR:
        return

    try:
        cache_path = Path(CACHE_DIR)
        cache_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{timestamp}_{message_type}_{message_id}.json"
        filepath = cache_path / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'type': message_type,
                'message_id': message_id,
                'data': data
            }, f, indent=2, ensure_ascii=False)

        print(f"[缓存] 已保存 {message_type} 消息: {filename}")
    except Exception as e:
        print(f"[缓存错误] 保存消息失败: {e}")

def update_daily_counter(counter_type="total"):
    """更新每日调用计数"""
    if not DEBUG_MODE or not CACHE_DIR:
        return

    valid_types = ["total", "success", "failed", "timeout", "retry"]
    if counter_type not in valid_types:
        return

    try:
        cache_path = Path(CACHE_DIR)
        today = datetime.now().strftime("%Y%m%d")
        counter_file = cache_path / f"CALLS_{today}.json"

        if counter_file.exists():
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                'date': today,
                'total': 0,
                'success': 0,
                'failed': 0,
                'timeout': 0,
                'retry': 0
            }

        data[counter_type] = data.get(counter_type, 0) + 1

        if counter_type in ["success", "failed", "timeout"]:
            data['total'] = data.get('total', 0) + 1

        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump({
                'date': today,
                'total': data.get('total', 0),
                'success': data.get('success', 0),
                'failed': data.get('failed', 0),
                'timeout': data.get('timeout', 0),
                'retry': data.get('retry', 0),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)

        type_names = {"total": "总调用", "success": "成功", "failed": "失败", "timeout": "超时", "retry": "重试"}
        print(f"[计数] {type_names[counter_type]} +1 (总计: 总={data['total']} 成功={data['success']} 失败={data['failed']} 超时={data['timeout']} 重试={data['retry']})")
    except Exception as e:
        print(f"[计数错误] 更新计数失败: {e}")

def start_file_watcher():
    """启动文件监控"""
    observer = Observer()
    observer.schedule(FileChangeHandler(), path='.', recursive=False)
    observer.start()
    return observer

def ensure_cache_dir():
    """确保缓存目录存在"""
    if not CACHE_DIR:
        return

    try:
        cache_path = Path(CACHE_DIR)
        cache_path.mkdir(parents=True, exist_ok=True)
        print(f"[缓存] 缓存目录已就绪: {CACHE_DIR}")
    except Exception as e:
        print(f"[缓存错误] 创建缓存目录失败: {e}")

def reload_env():
    """重新加载环境变量"""
    global DEBUG_MODE, CACHE_DIR, HTTP_PROXY, MAX_CONCURRENT_REQUESTS

    if 'CACHE_DIR' in os.environ:
        del os.environ['CACHE_DIR']
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    if 'MAX_CONCURRENT_REQUESTS' in os.environ:
        del os.environ['MAX_CONCURRENT_REQUESTS']

    load_env()

    DEBUG_MODE = check_debug_mode()
    CACHE_DIR = os.getenv("CACHE_DIR")
    HTTP_PROXY = os.getenv("HTTP_PROXY")
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

    if DEBUG_MODE:
        print("[调试] 调试模式已启用")
        if CACHE_DIR:
            ensure_cache_dir()
        else:
            print("[调试] 未配置缓存目录，消息不会被保存")

    if HTTP_PROXY:
        print(f"[代理] HTTP 代理已配置: {HTTP_PROXY}")

    print(f"[配置] 最大并发数: {MAX_CONCURRENT_REQUESTS}")
    print("[重载] 环境变量已重新加载")

def load_env():
    """加载环境变量"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

# 加载环境变量
load_env()

# 从环境变量加载Free API配置
FREE1_API_KEY = os.getenv("FREE1_API_KEY")
FREE2_API_KEY = os.getenv("FREE2_API_KEY")
FREE3_API_KEY = os.getenv("FREE3_API_KEY")

DEBUG_MODE = check_debug_mode()
CACHE_DIR = os.getenv("CACHE_DIR")
HTTP_PROXY = os.getenv("HTTP_PROXY")
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

def test_api_startup(api_name):
    """启动时测试API是否可用"""
    global FREE_APIS, HTTP_PROXY

    if api_name not in FREE_APIS:
        return False

    api_config = FREE_APIS[api_name]
    api_key = api_config["api_key"]
    base_url = api_config["base_url"]
    model = api_config.get("model", "gpt-3.5-turbo")
    use_proxy = api_config.get("use_proxy", False)

    print(f"[启动测试] 测试 {api_name} (模型: {model}, 代理: {use_proxy})...")

    try:
        url = f"{base_url}/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # 配置代理
        proxies = None
        if use_proxy and HTTP_PROXY:
            proxies = {
                "http": HTTP_PROXY,
                "https": HTTP_PROXY
            }

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 10
        }

        response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=30)

        api_config["last_test_time"] = datetime.now().isoformat()

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
        api_config["last_test_time"] = datetime.now().isoformat()
        api_config["last_test_result"] = f"error: {str(e)}"
        api_config["failure_count"] += 1
        print(f"[启动测试] {api_name} 测试失败: {e}")
        return False

def load_api_configs():
    """从.env加载API配置"""
    global FREE_APIS, FREE1_API_KEY, FREE2_API_KEY, FREE3_API_KEY

    # 直接配置API，不从free*目录读取
    FREE_APIS = {
        "free1": {
            "name": "free1",
            "api_key": FREE1_API_KEY,
            "base_url": "https://openrouter.ai",
            "model": "openrouter/free",
            "use_proxy": True,  # free1使用代理
            "available": False,
            "last_test_time": None,
            "last_test_result": None,
            "success_count": 0,
            "failure_count": 0
        },
        "free2": {
            "name": "free2",
            "api_key": FREE2_API_KEY,
            "base_url": "https://api.chatanywhere.tech",
            "model": "gpt-3.5-turbo",
            "use_proxy": False,  # free2不使用代理
            "available": False,
            "last_test_time": None,
            "last_test_result": None,
            "success_count": 0,
            "failure_count": 0
        },
        "free3": {
            "name": "free3",
            "api_key": FREE3_API_KEY,
            "base_url": "https://free.v36.cm",
            "model": "gpt-3.5-turbo",
            "use_proxy": False,  # free3不使用代理
            "available": False,
            "last_test_time": None,
            "last_test_result": None,
            "success_count": 0,
            "failure_count": 0
        }
    }

    print(f"[配置] 已加载 {len(FREE_APIS)} 个API配置")
    for api_name, api_config in FREE_APIS.items():
        print(f"[配置] {api_name}: API_KEY={api_config['api_key'][:10]}...{api_config['api_key'][-4:]}, BASE_URL={api_config['base_url']}, MODEL={api_config['model']}, USE_PROXY={api_config['use_proxy']}")

def test_all_apis_startup():
    """启动时测试所有API"""
    global FREE_APIS, AVAILABLE_APIS

    print("\n[启动测试] 开始测试所有API...")

    with API_LOCK:
        AVAILABLE_APIS.clear()

        for api_name in FREE_APIS:
            if FREE_APIS[api_name]["api_key"]:  # 只测试配置了API Key的
                if test_api_startup(api_name):
                    AVAILABLE_APIS.append(api_name)

        print(f"[启动测试] 测试完成，可用API: {len(AVAILABLE_APIS)}/{len(FREE_APIS)}")
        if AVAILABLE_APIS:
            print(f"[启动测试] 可用API列表: {list(AVAILABLE_APIS)}")

def get_next_available_api():
    """获取下一个可用的API"""
    global AVAILABLE_APIS

    with API_LOCK:
        if not AVAILABLE_APIS:
            return None

        # 获取队列中的第一个API
        api_name = AVAILABLE_APIS[0]

        # 将其移到队列末尾，实现轮换
        AVAILABLE_APIS.rotate(-1)

        return api_name

def execute_with_free_api(data, message_id):
    """使用Free API执行请求"""
    global FREE_APIS, HTTP_PROXY

    retry_count = 0
    last_error = None

    max_retries = 3
    timeout_base = 45
    timeout_retry = 60

    for attempt in range(max_retries):
        api_name = get_next_available_api()

        if not api_name:
            raise Exception("没有可用的Free API")

        api_config = FREE_APIS[api_name]
        api_key = api_config["api_key"]
        base_url = api_config["base_url"]
        model = api_config.get("model", "gpt-3.5-turbo")
        use_proxy = api_config.get("use_proxy", False)

        try:
            url = f"{base_url}/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            # 配置代理
            proxies = None
            if use_proxy and HTTP_PROXY:
                proxies = {
                    "http": HTTP_PROXY,
                    "https": HTTP_PROXY
                }

            current_timeout = timeout_retry if attempt > 0 else timeout_base
            attempt_str = f"(尝试 {attempt + 1}/{max_retries})" if attempt > 0 else ""
            print(f"[请求] 发送到 {api_name} (模型: {model}, 代理: {use_proxy}) {attempt_str} [超时: {current_timeout}s]")

            request_data = {
                "model": model,
                "messages": data.get("messages", []),
                "temperature": data.get("temperature", 0.7),
                "max_tokens": data.get("max_tokens", 2000),
                "top_p": data.get("top_p", 1),
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
            print(f"[请求] 成功 {attempt_str}")

            api_config["success_count"] += 1

            return result, retry_count

        except requests.exceptions.Timeout as e:
            last_error = e
            error_msg = f"[请求] 超时 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            print(error_msg)
            update_daily_counter("timeout")

            api_config["failure_count"] += 1

            if attempt < max_retries - 1:
                retry_count += 1
                update_daily_counter("retry")
                wait_time = 2 ** attempt
                print(f"[重试] 超时错误，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue

        except requests.exceptions.ConnectionError as e:
            last_error = e
            error_msg = f"[请求] 连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            print(error_msg)

            api_config["failure_count"] += 1

            if attempt < max_retries - 1:
                retry_count += 1
                update_daily_counter("retry")
                wait_time = 2 ** attempt
                print(f"[重试] 连接错误，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue

        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
            error_msg = f"[请求] HTTP错误 {status_code} (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            print(error_msg)

            api_config["failure_count"] += 1

            if 500 <= status_code < 600 and attempt < max_retries - 1:
                retry_count += 1
                update_daily_counter("retry")
                wait_time = 2 ** attempt
                print(f"[重试] 服务器错误，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
            else:
                break

        except Exception as e:
            last_error = e
            print(f"[请求] 失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")

            api_config["failure_count"] += 1
            break

    raise last_error

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    global RESTART_FLAG, DEBUG_MODE, CACHE_DIR, HTTP_PROXY, ACTIVE_REQUESTS, MAX_CONCURRENT_REQUESTS

    if RESTART_FLAG:
        print("\n[重启] 检测到配置变化，重新加载...")
        try:
            reload_env()
            RESTART_FLAG = False
            print("[重启] 重新加载完成")
        except Exception as e:
            print(f"[错误] 重新加载失败: {e}")
            return jsonify({"error": f"Configuration reload failed: {str(e)}"}), 500

    DEBUG_MODE = check_debug_mode()
    CACHE_DIR = os.getenv("CACHE_DIR")
    HTTP_PROXY = os.getenv("HTTP_PROXY")

    max_wait_time = 120
    wait_start = time.time()

    while True:
        with ACTIVE_LOCK:
            if ACTIVE_REQUESTS < MAX_CONCURRENT_REQUESTS:
                ACTIVE_REQUESTS += 1
                break

        elapsed = time.time() - wait_start
        if elapsed > max_wait_time:
            print(f"[并发] 等待超时 (已等待 {elapsed:.1f}s)")
            with LAST_ERROR_LOCK:
                LAST_ERROR["type"] = ERROR_TYPES["CONCURRENT_LIMIT"]
                LAST_ERROR["message"] = f"Concurrent limit exceeded: {ACTIVE_REQUESTS}/{MAX_CONCURRENT_REQUESTS}"
                LAST_ERROR["timestamp"] = datetime.now().isoformat()
            return jsonify({
                "error": "Server too busy - concurrent request limit exceeded",
                "details": f"Current: {ACTIVE_REQUESTS}/{MAX_CONCURRENT_REQUESTS}",
                "error_type": ERROR_TYPES["CONCURRENT_LIMIT"]
            }), 503

        if int(elapsed) % 5 == 0:
            print(f"[并发] 等待中... (已等待 {elapsed:.1f}s, 当前: {ACTIVE_REQUESTS}/{MAX_CONCURRENT_REQUESTS})")

        time.sleep(0.5)

    try:
        data = request.json
        message_id = str(uuid.uuid4())[:8]

        if DEBUG_MODE:
            save_message_cache("REQUEST", message_id, data)

        result, retry_count = execute_with_free_api(data, message_id)

        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion",
            "created": result.get("created", 0),
            "model": result.get("model", "gpt-3.5-turbo"),
            "choices": result.get("choices", []),
            "usage": result.get("usage", {}),
        }

        for choice in response_data.get("choices", []):
            message = choice.get("message", {})
            if not message.get("content") and message.get("reasoning"):
                message["content"] = message["reasoning"]

        with HISTORY_LOCK:
            CALL_HISTORY.append({"success": True, "timestamp": datetime.now()})

        if DEBUG_MODE:
            response_data["_retry_count"] = retry_count
            save_message_cache("RESPONSE", message_id, response_data)

        return jsonify(response_data)

    except requests.exceptions.RequestException as e:
        error_str = str(e).lower()
        error_type = ERROR_TYPES["API_ERROR"]

        if "timeout" in error_str or "timed out" in error_str:
            error_type = ERROR_TYPES["TIMEOUT"]
        elif "connection" in error_str or "refused" in error_str:
            error_type = ERROR_TYPES["UPSTREAM_UNREACHABLE"]
        elif "proxy" in error_str:
            error_type = ERROR_TYPES["PROXY_ERROR"]

        with LAST_ERROR_LOCK:
            LAST_ERROR["type"] = error_type
            LAST_ERROR["message"] = str(e)
            LAST_ERROR["timestamp"] = datetime.now().isoformat()

        error_response = {
            "error": f"Free API error: {str(e)}",
            "error_type": error_type
        }

        with HISTORY_LOCK:
            CALL_HISTORY.append({"success": False, "timestamp": datetime.now(), "error_type": error_type})

        if DEBUG_MODE:
            save_message_cache("ERROR", str(uuid.uuid4())[:8], error_response)
        return jsonify(error_response), 502
    except Exception as e:
        with LAST_ERROR_LOCK:
            LAST_ERROR["type"] = ERROR_TYPES["UNKNOWN"]
            LAST_ERROR["message"] = str(e)
            LAST_ERROR["timestamp"] = datetime.now().isoformat()

        error_response = {"error": str(e), "error_type": ERROR_TYPES["UNKNOWN"]}

        with HISTORY_LOCK:
            CALL_HISTORY.append({"success": False, "timestamp": datetime.now(), "error_type": ERROR_TYPES["UNKNOWN"]})

        if DEBUG_MODE:
            save_message_cache("ERROR", str(uuid.uuid4())[:8], error_response)
        return jsonify(error_response), 400
    finally:
        with ACTIVE_LOCK:
            ACTIVE_REQUESTS -= 1
        print(f"[并发] 请求完成 (当前: {ACTIVE_REQUESTS}/{MAX_CONCURRENT_REQUESTS})")

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出所有API支持的模型"""
    global FREE_APIS

    models = []

    for api_name, api_config in FREE_APIS.items():
        model = api_config.get("model", "gpt-3.5-turbo")
        models.append({
            "id": model,
            "object": "model",
            "owned_by": api_name,
            "permission": []
        })

    unique_models = []
    seen = set()
    for model in models:
        if model["id"] not in seen:
            seen.add(model["id"])
            unique_models.append(model)

    return jsonify({
        "object": "list",
        "data": unique_models
    })

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

@app.route('/health/upstream', methods=['GET'])
def health_upstream():
    """检查上游 API 连接状态"""
    with API_LOCK:
        available_count = len(AVAILABLE_APIS)
        total_count = len(FREE_APIS)
        api_list = list(AVAILABLE_APIS) if AVAILABLE_APIS else []

    return jsonify({
        "status": "ok",
        "upstream": "free-apis",
        "available_apis": available_count,
        "total_apis": total_count,
        "api_list": api_list
    })

@app.route('/debug/stats', methods=['GET'])
def debug_stats():
    """获取调试统计信息"""
    debug_enabled = check_debug_mode()
    cache_dir = os.getenv("CACHE_DIR")

    if not debug_enabled:
        return jsonify({"error": "Debug mode not enabled"}), 403

    if not cache_dir:
        return jsonify({"error": "Cache directory not configured"}), 400

    try:
        cache_path = Path(cache_dir)
        today = datetime.now().strftime("%Y%m%d")
        counter_file = cache_path / f"CALLS_{today}.json"

        if counter_file.exists():
            with open(counter_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            return jsonify(stats)
        else:
            return jsonify({
                "date": today,
                "total": 0,
                "success": 0,
                "failed": 0,
                "timeout": 0,
                "retry": 0,
                "last_updated": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug/apis', methods=['GET'])
def debug_apis():
    """获取所有API的状态"""
    return jsonify({
        "free_apis": FREE_APIS,
        "available_apis": list(AVAILABLE_APIS)
    })

def main():
    """主函数"""
    ensure_cache_dir()

    # 直接从.env加载API配置
    load_api_configs()

    # 启动时测试所有API
    test_all_apis_startup()

    # 启动API测试工作线程
    test_thread = threading.Thread(target=api_test_worker, daemon=True)
    test_thread.start()

    # 启动文件监控
    observer = start_file_watcher()

    port = int(os.getenv("PORT", "5000"))

    if is_port_in_use(port):
        print(f"[错误] 端口 {port} 已被占用")
        sys.exit(1)

    print(f"[启动] 多Free API代理服务启动在端口 {port}")
    print(f"[启动] 可用API: {len(AVAILABLE_APIS)}/{len(FREE_APIS)}")

    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[停止] 服务正在停止...")
        observer.stop()
        observer.join()
        print("[停止] 服务已停止")

def api_test_worker():
    """定期测试API的工作线程"""
    global API_TEST_INTERVAL

    while True:
        try:
            time.sleep(API_TEST_INTERVAL)
            test_all_apis_startup()
        except Exception as e:
            print(f"[测试] API测试工作线程错误: {e}")

if __name__ == "__main__":
    main()
