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
WATCHED_FILES = {'.env', 'multi_free_api_proxy.py'}
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
FREE_APIS = {}  # 存储所有检测到的Free API
AVAILABLE_APIS = deque()  # 可用的API队列
API_LOCK = threading.Lock()  # API队列锁
API_TEST_INTERVAL = 300  # API测试间隔(秒)

# 调用历史记录（用于重试决策）
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
        # 创建缓存目录
        cache_path = Path(CACHE_DIR)
        cache_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名: 时间戳_收发标志_消息id.json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{timestamp}_{message_type}_{message_id}.json"
        filepath = cache_path / filename

        # 保存消息
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
        print(f"[计数错误] 无效的计数器类型: {counter_type}")
        return

    try:
        cache_path = Path(CACHE_DIR)
        today = datetime.now().strftime("%Y%m%d")
        counter_file = cache_path / f"CALLS_{today}.json"

        # 读取当前计数
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

        # 增加计数
        data[counter_type] = data.get(counter_type, 0) + 1

        # 同时增加总调用次数（成功/失败/超时时增加，重试不增加总调用）
        if counter_type in ["success", "failed", "timeout"]:
            data['total'] = data.get('total', 0) + 1

        # 写入更新后的计数
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

        # 打印日志
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

    # 清除旧的环境变量
    if 'CACHE_DIR' in os.environ:
        del os.environ['CACHE_DIR']
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    if 'MAX_CONCURRENT_REQUESTS' in os.environ:
        del os.environ['MAX_CONCURRENT_REQUESTS']

    load_env()

    # 更新调试模式和缓存目录
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

# 从环境变量加载Free API Keys
FREE1_API_KEY = os.getenv("FREE1_API_KEY")
FREE2_API_KEY = os.getenv("FREE2_API_KEY")
FREE3_API_KEY = os.getenv("FREE3_API_KEY")

# 加载环境变量
load_env()

# 初始化调试模式和缓存目录
DEBUG_MODE = check_debug_mode()
CACHE_DIR = os.getenv("CACHE_DIR")
HTTP_PROXY = os.getenv("HTTP_PROXY")
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

def detect_free_apis():
    """检测free_api_test目录下的所有Free API"""
    global FREE_APIS

    free_api_test_dir = Path("free_api_test")
    if not free_api_test_dir.exists():
        print(f"[检测] free_api_test目录不存在")
        return

    # 查找所有以"free"开头的目录
    free_dirs = [d for d in free_api_test_dir.iterdir() if d.is_dir() and d.name.startswith("free")]

    if not free_dirs:
        print(f"[检测] 未找到任何free API目录")
        return

    print(f"[检测] 找到 {len(free_dirs)} 个free API目录")

    for free_dir in free_dirs:
        api_name = free_dir.name
        test_api_file = free_dir / "test_api.py"

        if not test_api_file.exists():
            print(f"[检测] {api_name} 缺少test_api.py文件，跳过")
            continue

        # 尝试从test_api.py中提取API配置
        try:
            with open(test_api_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取API_KEY (支持两种格式: API_KEY 或 openai.api_key)
            api_key = None
            for line in content.split('\n'):
                if ('API_KEY' in line or 'api_key' in line) and '=' in line and not line.strip().startswith('#'):
                    # 提取引号中的内容
                    import re
                    match = re.search(r'["\']([^"\']+)["\']', line)
                    if match:
                        api_key = match.group(1)
                        break

            # 提取BASE_URL或base_url (支持两种格式: BASE_URL 或 openai.base_url)
            base_url = None
            for line in content.split('\n'):
                if ('BASE_URL' in line or 'base_url' in line) and '=' in line and not line.strip().startswith('#'):
                    import re
                    match = re.search(r'["\']([^"\']+)["\']', line)
                    if match:
                        base_url = match.group(1)
                        # 如果base_url以/v1/结尾，去掉/v1/部分
                        if base_url.endswith('/v1/'):
                            base_url = base_url[:-4]
                        break

            # 提取支持的模型列表
            supported_models = []
            readme_files = ['README.md', 'readme.txt', 'README.txt']
            for readme_file in readme_files:
                readme_path = free_dir / readme_file
                if readme_path.exists():
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme_content = f.read()
                        # 从README中提取模型列表
                        model_pattern = r'\b(gpt-[\w.-]+|deepseek-[\w.-]+)\b'
                        models = re.findall(model_pattern, readme_content, re.IGNORECASE)
                        if models:
                            supported_models = list(set([m.lower() for m in models]))
                            break

            if api_key and base_url:
                FREE_APIS[api_name] = {
                    "name": api_name,
                    "api_key": api_key,
                    "base_url": base_url,
                    "available": False,
                    "last_test_time": None,
                    "last_test_result": None,
                    "success_count": 0,
                    "failure_count": 0,
                    "supported_models": supported_models if supported_models else ["gpt-3.5-turbo"]
                }
                print(f"[检测] {api_name}: API_KEY={api_key[:10]}...{api_key[-4:]}, BASE_URL={base_url}")
                print(f"[检测] {api_name}: 支持的模型: {', '.join(supported_models) if supported_models else 'gpt-3.5-turbo'}")
            else:
                print(f"[检测] {api_name} 无法提取API配置，跳过")
        except Exception as e:
            print(f"[检测] {api_name} 读取配置失败: {e}")

def test_free_api(api_name):
    """测试指定的Free API是否可用"""
    global FREE_APIS

    if api_name not in FREE_APIS:
        print(f"[测试] {api_name} 不存在")
        return False

    api_config = FREE_APIS[api_name]
    api_key = api_config["api_key"]
    base_url = api_config["base_url"]
    supported_models = api_config.get("supported_models", ["gpt-3.5-turbo"])

    # 使用支持的第一个模型进行测试
    test_model = supported_models[0] if supported_models else "gpt-3.5-turbo"

    print(f"[测试] 测试 {api_name} (模型: {test_model})...")

    try:
        # 构建测试请求
        url = f"{base_url}/v1/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            "model": test_model,
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 10
        }

        # 发送测试请求
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        # 更新测试结果
        api_config["last_test_time"] = datetime.now().isoformat()

        if response.status_code == 200:
            api_config["available"] = True
            api_config["last_test_result"] = "success"
            api_config["success_count"] += 1
            print(f"[测试] {api_name} 可用")
            return True
        else:
            api_config["available"] = False
            api_config["last_test_result"] = f"failed: {response.status_code}"
            api_config["failure_count"] += 1
            print(f"[测试] {api_name} 不可用: {response.status_code}")
            return False
    except Exception as e:
        api_config["available"] = False
        api_config["last_test_time"] = datetime.now().isoformat()
        api_config["last_test_result"] = f"error: {str(e)}"
        api_config["failure_count"] += 1
        print(f"[测试] {api_name} 测试失败: {e}")
        return False

def test_all_free_apis():
    """测试所有检测到的Free API"""
    global FREE_APIS, AVAILABLE_APIS

    print("\n[测试] 开始测试所有Free API...")

    with API_LOCK:
        # 清空可用API队列
        AVAILABLE_APIS.clear()

        # 测试每个API
        for api_name in FREE_APIS:
            if test_free_api(api_name):
                AVAILABLE_APIS.append(api_name)

        print(f"[测试] 测试完成，可用API: {len(AVAILABLE_APIS)}/{len(FREE_APIS)}")
        if AVAILABLE_APIS:
            print(f"[测试] 可用API列表: {list(AVAILABLE_APIS)}")

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

def api_test_worker():
    """定期测试API的工作线程"""
    global API_TEST_INTERVAL

    while True:
        time.sleep(API_TEST_INTERVAL)
        test_all_free_apis()

def execute_with_free_api(data, message_id):
    """使用Free API执行请求"""
    global FREE_APIS

    retry_count = 0
    last_error = None

    # 重试配置
    max_retries = 3
    timeout_base = 45
    timeout_retry = 60

    for attempt in range(max_retries):
        # 获取下一个可用的API
        api_name = get_next_available_api()

        if not api_name:
            raise Exception("没有可用的Free API")

        api_config = FREE_APIS[api_name]
        api_key = api_config["api_key"]
        base_url = api_config["base_url"]
        supported_models = api_config.get("supported_models", ["gpt-3.5-turbo"])

        # 使用API支持的第一个模型，忽略原始请求中的model参数
        model = supported_models[0] if supported_models else "gpt-3.5-turbo"

        try:
            # 构建请求
            url = f"{base_url}/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            # 根据重试次数调整超时时间
            current_timeout = timeout_retry if attempt > 0 else timeout_base
            attempt_str = f"(尝试 {attempt + 1}/{max_retries})" if attempt > 0 else ""
            print(f"[请求] 发送到 {api_name} (模型: {model}) {attempt_str} [超时: {current_timeout}s]")

            # 构建请求数据，使用API支持的模型
            request_data = {
                "model": model,
                "messages": data.get("messages", []),
                "temperature": data.get("temperature", 0.7),
                "max_tokens": data.get("max_tokens", 2000),
                "top_p": data.get("top_p", 1),
            }

            # 发送请求
            response = session.post(
                url,
                json=request_data,
                headers=headers,
                timeout=current_timeout
            )
            response.raise_for_status()

            result = response.json()
            print(f"[请求] 成功 {attempt_str}")

            # 更新成功计数
            api_config["success_count"] += 1

            return result, retry_count

        except requests.exceptions.Timeout as e:
            last_error = e
            error_msg = f"[请求] 超时 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            print(error_msg)
            update_daily_counter("timeout")

            # 更新失败计数
            api_config["failure_count"] += 1

            # 超时错误总是重试（除了最后一次）
            if attempt < max_retries - 1:
                retry_count += 1
                update_daily_counter("retry")
                wait_time = 2 ** attempt  # 指数退避: 1s, 2s, 4s
                print(f"[重试] 超时错误，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue

        except requests.exceptions.ConnectionError as e:
            last_error = e
            error_msg = f"[请求] 连接错误 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            print(error_msg)

            # 更新失败计数
            api_config["failure_count"] += 1

            # 连接错误也应该重试
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

            # 更新失败计数
            api_config["failure_count"] += 1

            # 5xx 错误重试，4xx 错误不重试
            if 500 <= status_code < 600 and attempt < max_retries - 1:
                retry_count += 1
                update_daily_counter("retry")
                wait_time = 2 ** attempt
                print(f"[重试] 服务器错误，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
            else:
                # 4xx 错误或已是最后一次尝试
                break

        except Exception as e:
            last_error = e
            print(f"[请求] 失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")

            # 更新失败计数
            api_config["failure_count"] += 1

            # 其他错误不重试
            break

    # 所有尝试都失败了
    raise last_error

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    global RESTART_FLAG, DEBUG_MODE, CACHE_DIR, HTTP_PROXY, ACTIVE_REQUESTS, MAX_CONCURRENT_REQUESTS

    # 检查是否需要重启
    if RESTART_FLAG:
        print("\n[重启] 检测到配置变化，重新加载...")
        try:
            reload_env()
            RESTART_FLAG = False
            print("[重启] 重新加载完成")
        except Exception as e:
            print(f"[错误] 重新加载失败: {e}")
            return jsonify({"error": f"Configuration reload failed: {str(e)}"}), 500

    # 检查调试模式
    DEBUG_MODE = check_debug_mode()
    CACHE_DIR = os.getenv("CACHE_DIR")
    HTTP_PROXY = os.getenv("HTTP_PROXY")

    # 检查并发限制（带超时）
    max_wait_time = 120  # 最多等待120秒
    wait_start = time.time()

    while True:
        with ACTIVE_LOCK:
            if ACTIVE_REQUESTS < MAX_CONCURRENT_REQUESTS:
                ACTIVE_REQUESTS += 1
                break

        # 检查是否超时
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

        # 每5秒打印一次等待状态
        if int(elapsed) % 5 == 0:
            print(f"[并发] 等待中... (已等待 {elapsed:.1f}s, 当前: {ACTIVE_REQUESTS}/{MAX_CONCURRENT_REQUESTS})")

        time.sleep(0.5)  # 减少轮询间隔，更快响应

    try:
        data = request.json
        message_id = str(uuid.uuid4())[:8]

        # 保存请求消息
        if DEBUG_MODE:
            save_message_cache("REQUEST", message_id, data)

        # 执行请求（带重试机制）
        result, retry_count = execute_with_free_api(data, message_id)

        # 转换为 OpenAI 兼容格式
        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion",
            "created": result.get("created", 0),
            "model": result.get("model", "gpt-3.5-turbo"),
            "choices": result.get("choices", []),
            "usage": result.get("usage", {}),
        }

        # 如果 content 为空但有 reasoning,则将 reasoning 复制到 content
        for choice in response_data.get("choices", []):
            message = choice.get("message", {})
            if not message.get("content") and message.get("reasoning"):
                message["content"] = message["reasoning"]

        # 记录调用历史
        with HISTORY_LOCK:
            CALL_HISTORY.append({"success": True, "timestamp": datetime.now()})

        # 保存响应消息
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

        # 记录调用历史
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

        # 记录调用历史
        with HISTORY_LOCK:
            CALL_HISTORY.append({"success": False, "timestamp": datetime.now(), "error_type": ERROR_TYPES["UNKNOWN"]})

        if DEBUG_MODE:
            save_message_cache("ERROR", str(uuid.uuid4())[:8], error_response)
        return jsonify(error_response), 400
    finally:
        # 释放并发槽位
        with ACTIVE_LOCK:
            ACTIVE_REQUESTS -= 1
        print(f"[并发] 请求完成 (当前: {ACTIVE_REQUESTS}/{MAX_CONCURRENT_REQUESTS})")

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出所有API支持的模型"""
    global FREE_APIS

    models = []

    # 收集所有API支持的模型
    for api_name, api_config in FREE_APIS.items():
        supported_models = api_config.get("supported_models", ["gpt-3.5-turbo"])
        for model in supported_models:
            models.append({
                "id": model,
                "object": "model",
                "owned_by": api_name,
                "permission": []
            })

    # 去重
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
    # 实时检查调试模式
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
    # 确保缓存目录存在
    ensure_cache_dir()

    # 检测所有Free API
    detect_free_apis()

    # 测试所有Free API
    test_all_free_apis()

    # 启动API测试工作线程
    test_thread = threading.Thread(target=api_test_worker, daemon=True)
    test_thread.start()

    # 启动文件监控
    observer = start_file_watcher()

    # 获取配置的端口
    port = int(os.getenv("PORT", "5000"))

    # 检查端口是否被占用
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

if __name__ == "__main__":
    main()
