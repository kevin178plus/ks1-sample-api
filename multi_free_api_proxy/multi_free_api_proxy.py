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
MAX_CONSECUTIVE_FAILURES = 3  # 连续失败次数阈值，超过此值标记API无效

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
                    "consecutive_failures": 0,  # 连续失败次数
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

def mark_api_failure(api_name):
    """标记API失败，连续失败超过阈值则从可用列表移除"""
    global FREE_APIS, AVAILABLE_APIS, MAX_CONSECUTIVE_FAILURES
    
    if api_name not in FREE_APIS:
        return
    
    api_config = FREE_APIS[api_name]
    api_config["consecutive_failures"] = api_config.get("consecutive_failures", 0) + 1
    api_config["failure_count"] += 1
    
    consecutive = api_config["consecutive_failures"]
    print(f"[API状态] {api_name} 连续失败次数: {consecutive}/{MAX_CONSECUTIVE_FAILURES}")
    
    if consecutive >= MAX_CONSECUTIVE_FAILURES:
        with API_LOCK:
            if api_name in AVAILABLE_APIS:
                AVAILABLE_APIS.remove(api_name)
                api_config["available"] = False
                api_config["last_test_result"] = f"marked invalid after {consecutive} consecutive failures"
                print(f"[API状态] {api_name} 已标记为无效（连续失败{consecutive}次）")
                print(f"[API状态] 剩余可用API: {list(AVAILABLE_APIS)}")

def mark_api_success(api_name):
    """标记API成功，重置连续失败计数"""
    global FREE_APIS
    
    if api_name not in FREE_APIS:
        return
    
    api_config = FREE_APIS[api_name]
    api_config["consecutive_failures"] = 0
    api_config["success_count"] += 1
    
    # 如果API不在可用列表中，重新添加
    with API_LOCK:
        if api_name not in AVAILABLE_APIS and api_config.get("api_key"):
            AVAILABLE_APIS.append(api_name)
            api_config["available"] = True
            print(f"[API状态] {api_name} 已恢复并重新加入可用列表")

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

            # 标记成功，重置连续失败计数
            mark_api_success(api_name)

            return result, retry_count

        except requests.exceptions.Timeout as e:
            last_error = e
            error_msg = f"[请求] 超时 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            print(error_msg)
            update_daily_counter("timeout")

            # 标记失败
            mark_api_failure(api_name)

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

            # 标记失败
            mark_api_failure(api_name)

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

            # 标记失败
            mark_api_failure(api_name)

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

            # 标记失败
            mark_api_failure(api_name)

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

@app.route('/debug/concurrency', methods=['GET'])
def debug_concurrency():
    """获取并发状态和调用历史"""
    debug_enabled = check_debug_mode()
    if not debug_enabled:
        return jsonify({"error": "Debug mode not enabled"}), 403
    
    with ACTIVE_LOCK:
        active = ACTIVE_REQUESTS
    
    with HISTORY_LOCK:
        history = list(CALL_HISTORY)
        history_data = [
            {
                "success": call["success"],
                "timestamp": call["timestamp"].isoformat(),
                "date": call["timestamp"].date().isoformat(),
                "error_type": call.get("error_type", None)
            }
            for call in history
        ]
    
    with LAST_ERROR_LOCK:
        last_error = dict(LAST_ERROR)
    
    today = datetime.now().date()
    today_calls = [call for call in history if call["timestamp"].date() == today]
    today_success = sum(1 for call in today_calls if call["success"])
    today_failed = sum(1 for call in today_calls if not call["success"])
    
    return jsonify({
        "concurrency": {
            "active_requests": active,
            "max_concurrent": MAX_CONCURRENT_REQUESTS,
            "available_slots": MAX_CONCURRENT_REQUESTS - active
        },
        "call_history": history_data,
        "today_stats": {
            "total": len(today_calls),
            "success": today_success,
            "failed": today_failed
        },
        "last_error": last_error,
        "free_apis": {
            "total": len(FREE_APIS),
            "available": len(AVAILABLE_APIS),
            "api_list": list(AVAILABLE_APIS)
        }
    })

@app.route('/debug', methods=['GET'])
def debug_page():
    """调试页面"""
    debug_enabled = check_debug_mode()
    if not debug_enabled:
        return "Debug mode not enabled", 403
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>多Free API代理调试面板</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 20px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            h1, h2 {
                color: #333;
                border-bottom: 2px solid #007bff;
                padding-bottom: 10px;
            }
            .stats {
                background-color: #e7f3ff;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .stat-item {
                margin: 10px 0;
                font-size: 16px;
            }
            .stat-label {
                font-weight: bold;
                color: #333;
            }
            .stat-value {
                color: #007bff;
                font-size: 24px;
                font-weight: bold;
            }
            .refresh-btn {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }
            .refresh-btn:hover {
                background-color: #0056b3;
            }
            .timestamp {
                color: #666;
                font-size: 12px;
                margin-top: 10px;
            }
            .error-status {
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }
            .error-status h3 {
                color: #856404;
                margin-top: 0;
            }
            .error-item {
                margin: 8px 0;
                font-size: 14px;
            }
            .error-label {
                font-weight: bold;
                color: #856404;
            }
            .error-value {
                color: #333;
            }
            .error-status.timeout {
                background-color: #fff3cd;
                border-color: #ffc107;
            }
            .error-status.upstream_unreachable {
                background-color: #f8d7da;
                border-color: #f5c6cb;
            }
            .error-status.api_error {
                background-color: #f8d7da;
                border-color: #f5c6cb;
            }
            .error-status.concurrent_limit {
                background-color: #cce5ff;
                border-color: #b8daff;
            }
            .error-status.proxy_error {
                background-color: #e2e3e5;
                border-color: #d6d8db;
            }
            .chat-container {
                display: flex;
                flex-direction: column;
                height: 500px;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin: 20px 0;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background-color: #f9f9f9;
            }
            .message {
                margin: 10px 0;
                padding: 10px;
                border-radius: 8px;
            }
            .message.user {
                background-color: #e3f2fd;
                text-align: right;
                margin-left: 20%;
            }
            .message.assistant {
                background-color: #f1f8e9;
                margin-right: 20%;
            }
            .message.error {
                background-color: #ffebee;
                color: #c62828;
                margin-right: 20%;
            }
            .message .time {
                font-size: 11px;
                color: #666;
                margin-top: 5px;
            }
            .message .latency {
                font-size: 11px;
                color: #007bff;
                font-weight: bold;
            }
            .chat-input {
                display: flex;
                padding: 10px;
                border-top: 1px solid #ddd;
                background-color: white;
            }
            .chat-input input {
                flex: 1;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            .chat-input button {
                margin-left: 10px;
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .chat-input button:hover {
                background-color: #0056b3;
            }
            .chat-input button:disabled {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .loading {
                color: #666;
                font-style: italic;
            }
            .tabs {
                display: flex;
                border-bottom: 1px solid #ddd;
                margin-bottom: 20px;
            }
            .tab {
                padding: 10px 20px;
                cursor: pointer;
                border-bottom: 2px solid transparent;
            }
            .tab.active {
                border-bottom-color: #007bff;
                color: #007bff;
                font-weight: bold;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .api-status {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
            }
            .api-status.available {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
            }
            .api-status.unavailable {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 多Free API代理调试面板</h1>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('stats')">统计信息</div>
                <div class="tab" onclick="showTab('apis')">API状态</div>
                <div class="tab" onclick="showTab('chat')">测试聊天</div>
            </div>
            
            <!-- 统计信息标签页 -->
            <div id="stats-tab" class="tab-content active">
                <div class="stats">
                    <div class="stat-item">
                        <span class="stat-label">总调用次数:</span>
                        <span class="stat-value" id="totalCount">-</span>
                        <span> 次</span>
                    </div>
                    <div class="stat-item" style="display: flex; gap: 20px;">
                        <div>
                            <span class="stat-label">✅ 成功:</span>
                            <span class="stat-value" id="successCount" style="color: #28a745;">-</span>
                            <span> 次</span>
                        </div>
                        <div>
                            <span class="stat-label">❌ 失败:</span>
                            <span class="stat-value" id="failedCount" style="color: #dc3545;">-</span>
                            <span> 次</span>
                        </div>
                        <div>
                            <span class="stat-label">⏱️ 超时:</span>
                            <span class="stat-value" id="timeoutCount" style="color: #ffc107;">-</span>
                            <span> 次</span>
                        </div>
                        <div>
                            <span class="stat-label">🔄 重试:</span>
                            <span class="stat-value" id="retryCount" style="color: #17a2b8;">-</span>
                            <span> 次</span>
                        </div>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">日期:</span>
                        <span id="date">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">最后更新:</span>
                        <span id="lastUpdated">-</span>
                    </div>
                    <div class="timestamp" id="refreshTime"></div>
                </div>
                
                <div id="error-status" class="error-status" style="display: none;">
                    <h3>⚠️ 当前状态</h3>
                    <div class="error-item">
                        <span class="error-label">错误类型:</span>
                        <span id="errorType" class="error-value">-</span>
                    </div>
                    <div class="error-item">
                        <span class="error-label">错误信息:</span>
                        <span id="errorMessage" class="error-value">-</span>
                    </div>
                    <div class="error-item">
                        <span class="error-label">发生时间:</span>
                        <span id="errorTime" class="error-value">-</span>
                    </div>
                </div>
                
                <button class="refresh-btn" onclick="refreshStats()">刷新统计</button>
            </div>
            
            <!-- API状态标签页 -->
            <div id="apis-tab" class="tab-content">
                <h2>📡 Free API 状态</h2>
                <div id="apiList"></div>
                <button class="refresh-btn" onclick="refreshApis()" style="margin-top: 15px;">刷新API状态</button>
            </div>
            
            <!-- 测试聊天标签页 -->
            <div id="chat-tab" class="tab-content">
                <h2>💬 AI 聊天测试</h2>
                <div style="margin-bottom: 15px; padding: 10px; background-color: #f0f8ff; border-radius: 5px; font-size: 13px; color: #666;">
                    <strong>📝 参数说明:</strong> max_tokens 控制AI回复的最大长度,默认1000。
                </div>
                <div style="margin-bottom: 10px;">
                    <label for="maxTokensInput" style="font-weight: bold; color: #333;">Max Tokens:</label>
                    <input type="number" id="maxTokensInput" value="1000" min="100" max="4000" step="100" 
                           style="padding: 5px; border: 1px solid #ddd; border-radius: 4px; width: 100px; margin-left: 10px;">
                    <span style="color: #666; font-size: 12px;">(默认: 1000, 范围: 100-4000)</span>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chatMessages"></div>
                    <div class="chat-input">
                        <input type="text" id="messageInput" placeholder="输入您的问题..." onkeypress="handleKeyPress(event)">
                        <button id="sendBtn" onclick="sendMessage()">发送</button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function showTab(tabName) {
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                document.getElementById(tabName + '-tab').classList.add('active');
                event.target.classList.add('active');
            }
            
            function refreshStats() {
                Promise.all([
                    fetch('/debug/stats').then(r => r.json()),
                    fetch('/debug/concurrency').then(r => r.json())
                ])
                    .then(([statsData, concurrencyData]) => {
                        document.getElementById('totalCount').textContent = statsData.total || 0;
                        document.getElementById('successCount').textContent = statsData.success || 0;
                        document.getElementById('failedCount').textContent = statsData.failed || 0;
                        document.getElementById('timeoutCount').textContent = statsData.timeout || 0;
                        document.getElementById('retryCount').textContent = statsData.retry || 0;
                        document.getElementById('date').textContent = statsData.date || '-';
                        document.getElementById('lastUpdated').textContent = statsData.last_updated ? new Date(statsData.last_updated).toLocaleString() : '-';
                        document.getElementById('refreshTime').textContent = '刷新于: ' + new Date().toLocaleTimeString();
                        
                        const errorStatus = document.getElementById('error-status');
                        const lastError = concurrencyData.last_error;
                        
                        if (lastError && lastError.type && lastError.type !== 'none') {
                            errorStatus.style.display = 'block';
                            errorStatus.className = 'error-status ' + lastError.type;
                            
                            const errorTypeNames = {
                                'none': '无错误',
                                'timeout': '⏱️ 超时',
                                'upstream_unreachable': '🔴 上游服务器无法连接',
                                'api_error': '❌ API 错误',
                                'concurrent_limit': '⚠️ 并发限制',
                                'proxy_error': '🔗 代理错误',
                                'unknown': '❓ 未知错误'
                            };
                            
                            document.getElementById('errorType').textContent = errorTypeNames[lastError.type] || lastError.type;
                            document.getElementById('errorMessage').textContent = lastError.message || '-';
                            document.getElementById('errorTime').textContent = lastError.timestamp ? new Date(lastError.timestamp).toLocaleString() : '-';
                        } else {
                            errorStatus.style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('totalCount').textContent = '错误';
                    });
            }
            
            function refreshApis() {
                fetch('/debug/apis')
                    .then(r => r.json())
                    .then(data => {
                        const apiListDiv = document.getElementById('apiList');
                        apiListDiv.innerHTML = '';
                        
                        const apis = data.free_apis || {};
                        const availableApis = data.available_apis || [];
                        
                        for (const [name, config] of Object.entries(apis)) {
                            const isAvailable = availableApis.includes(name);
                            const div = document.createElement('div');
                            div.className = 'api-status ' + (isAvailable ? 'available' : 'unavailable');
                            div.innerHTML = `
                                <strong>${name}</strong>
                                <span style="float: right;">${isAvailable ? '✅ 可用' : '❌ 不可用'}</span>
                                <br><small>模型: ${config.supported_models ? config.supported_models.join(', ') : 'gpt-3.5-turbo'}</small>
                                <br><small>成功: ${config.success_count || 0} | 失败: ${config.failure_count || 0}</small>
                                ${config.last_test_result ? '<br><small>最后测试: ' + config.last_test_result + '</small>' : ''}
                            `;
                            apiListDiv.appendChild(div);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('apiList').innerHTML = '<p style="color: red;">获取API状态失败</p>';
                    });
            }
            
            function addMessage(role, content, latency = null, error = false) {
                const messagesContainer = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${role} ${error ? 'error' : ''}`;
                
                let contentHtml = content.replace(/\\n/g, '<br>');
                let metadataHtml = `<div class="time">${new Date().toLocaleString()}</div>`;
                
                if (latency !== null) {
                    metadataHtml += `<div class="latency">响应时间: ${latency}ms</div>`;
                }
                
                messageDiv.innerHTML = contentHtml + metadataHtml;
                messagesContainer.appendChild(messageDiv);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                const sendBtn = document.getElementById('sendBtn');
                const maxTokensInput = document.getElementById('maxTokensInput');
                
                if (!message) return;
                
                addMessage('user', message);
                
                input.value = '';
                sendBtn.disabled = true;
                sendBtn.textContent = '发送中...';
                
                addMessage('assistant', '<span class="loading">AI 正在思考...</span>', null, false);
                
                const startTime = Date.now();
                
                fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: 'any-model',
                        messages: [
                            { role: 'user', content: message }
                        ],
                        max_tokens: parseInt(maxTokensInput.value) || 1000,
                        temperature: 0.7
                    })
                })
                .then(response => {
                    const endTime = Date.now();
                    const latency = endTime - startTime;
                    
                    const loadingMessages = document.querySelectorAll('.message .loading');
                    loadingMessages.forEach(msg => msg.parentElement.remove());
                    
                    if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.error || `HTTP ${response.status}`);
                        });
                    }
                    
                    return response.json();
                })
                .then(data => {
                    const endTime = Date.now();
                    const latency = endTime - startTime;
                    
                    const content = data.choices?.[0]?.message?.content || '无回复内容';
                    addMessage('assistant', content, latency);
                })
                .catch(error => {
                    const endTime = Date.now();
                    const latency = endTime - startTime;
                    
                    const loadingMessages = document.querySelectorAll('.message .loading');
                    loadingMessages.forEach(msg => msg.parentElement.remove());
                    
                    addMessage('assistant', `错误: ${error.message}`, latency, true);
                })
                .finally(() => {
                    sendBtn.disabled = false;
                    sendBtn.textContent = '发送';
                });
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            // 页面加载时刷新统计
            refreshStats();
            refreshApis();
            
            // 每30秒自动刷新统计
            setInterval(refreshStats, 30000);
            
            // 初始化聊天界面
            document.getElementById('chatMessages').innerHTML = '<div class="message assistant">欢迎使用多Free API聊天测试！您可以在这里直接测试代理功能。</div>';
        </script>
    </body>
    </html>
    """
    return html

def main():
    """主函数"""
    # 确保缓存目录存在
    ensure_cache_dir()

    # 检测所有Free API
    detect_free_apis()

    # 测试所有Free API（仅启动时测试一次）
    test_all_free_apis()

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
    print(f"[启动] API连续失败{MAX_CONSECUTIVE_FAILURES}次后将自动标记为无效")

    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[停止] 服务正在停止...")
        observer.stop()
        observer.join()
        print("[停止] 服务已停止")

if __name__ == "__main__":
    main()
