import os
import json
import sys
import time
import uuid
import threading
import socket
from pathlib import Path
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# 配置 requests 会话，使用连接池和重试策略
session = requests.Session()

# 配置重试策略
retry_strategy = Retry(
    total=0,  # 由我们的 execute_with_retry 函数处理重试
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST", "GET"]
)

adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
session.mount("http://", adapter)
session.mount("https://", adapter)

# 全局变量用于重启控制
RESTART_FLAG = False
WATCHED_FILES = {'.env', 'local_api_proxy.py'}
DEBUG_MODE = False
CACHE_DIR = None
HTTP_PROXY = None

# 并发控制相关
MAX_CONCURRENT_REQUESTS = 5  # 默认最大并发数
ACTIVE_REQUESTS = 0
REQUEST_QUEUE = deque()
QUEUE_LOCK = threading.Lock()
ACTIVE_LOCK = threading.Lock()

# 调用历史记录（用于重试决策）
CALL_HISTORY = deque(maxlen=10)
HISTORY_LOCK = threading.Lock()

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
        
        # 更新每日调用计数
        if message_type == "RESPONSE":
            update_daily_counter("success")
        elif message_type == "ERROR":
            error_data = data.get('error', {}) if isinstance(data, dict) else {}
            error_msg = str(error_data.get('message', '')).lower()
            if 'timeout' in error_msg or '超时' in error_msg:
                update_daily_counter("timeout")
            else:
                update_daily_counter("failed")
    except Exception as e:
        print(f"[缓存错误] 保存消息失败: {e}")

def update_daily_counter(counter_type="total"):
    """更新每日调用计数
    
    Args:
        counter_type: 计数器类型，可选值:
            - "total": 总调用次数
            - "success": 成功次数
            - "failed": 失败次数
            - "timeout": 超时次数
            - "retry": 重试次数
    """
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
    global API_KEY, DEBUG_MODE, CACHE_DIR, HTTP_PROXY, MAX_CONCURRENT_REQUESTS
    # 清除旧的环境变量
    if 'OPENROUTER_API_KEY' in os.environ:
        del os.environ['OPENROUTER_API_KEY']
    if 'CACHE_DIR' in os.environ:
        del os.environ['CACHE_DIR']
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    if 'MAX_CONCURRENT_REQUESTS' in os.environ:
        del os.environ['MAX_CONCURRENT_REQUESTS']
    
    load_env()
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in .env file")
    
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
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

API_KEY = os.getenv("OPENROUTER_API_KEY")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
HTTP_PROXY = os.getenv("HTTP_PROXY")
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

if not API_KEY and not TEST_MODE:
    raise ValueError("OPENROUTER_API_KEY not found in .env file and TEST_MODE is not enabled")

# 初始化调试模式和缓存目录
DEBUG_MODE = check_debug_mode()
CACHE_DIR = os.getenv("CACHE_DIR")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    global RESTART_FLAG, API_KEY, DEBUG_MODE, CACHE_DIR, HTTP_PROXY, ACTIVE_REQUESTS, MAX_CONCURRENT_REQUESTS
    
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
        result, retry_count = execute_with_retry(data, message_id)
        
        # 转换为 OpenAI 兼容格式
        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion",
            "created": result.get("created", 0),
            "model": result.get("model", "openrouter/free"),
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
            "error": f"OpenRouter API error: {str(e)}",
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
    """列出可用模型"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "openrouter/free",
                "object": "model",
                "owned_by": "openrouter",
                "permission": []
            }
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

@app.route('/health/upstream', methods=['GET'])
def health_upstream():
    """检查上游 API 连接状态"""
    if TEST_MODE:
        return jsonify({
            "status": "ok",
            "mode": "test",
            "upstream": "simulated"
        })
    
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "LocalAPIProxy",
        }
        
        proxies = None
        if HTTP_PROXY:
            proxies = {
                "http": HTTP_PROXY,
                "https": HTTP_PROXY
            }
        
        # 发送一个最小的测试请求
        test_payload = {
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 10,
        }
        
        start_time = time.time()
        response = session.post(
            OPENROUTER_API_URL,
            json=test_payload,
            headers=headers,
            proxies=proxies,
            timeout=10
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            return jsonify({
                "status": "ok",
                "upstream": "reachable",
                "response_time_ms": int(elapsed * 1000)
            })
        else:
            return jsonify({
                "status": "error",
                "upstream": "error",
                "http_status": response.status_code,
                "response_time_ms": int(elapsed * 1000)
            }), 502
    
    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "upstream": "timeout",
            "message": "Upstream API timeout"
        }), 504
    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "error",
            "upstream": "unreachable",
            "message": "Cannot connect to upstream API"
        }), 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "upstream": "error",
            "message": str(e)
        }), 500

def should_retry():
    """判断是否应该重试
    条件：
    1. 今天前3次调用中有失败
    2. 最近3次调用中有成功
    """
    with HISTORY_LOCK:
        if len(CALL_HISTORY) == 0:
            return False
        
        today = datetime.now().date()
        today_calls = [call for call in CALL_HISTORY if call["timestamp"].date() == today]
        
        # 条件1：今天前3次调用中有失败
        if len(today_calls) < 3:
            has_failure_today = any(not call["success"] for call in today_calls)
            if has_failure_today:
                return True
        
        # 条件2：最近3次调用中有成功
        has_recent_success = any(call["success"] for call in CALL_HISTORY)
        if has_recent_success:
            return True
        
        return False

def execute_with_retry(data, message_id):
    """执行请求，如果失败则重试一次
    返回: (result, retry_count)
    """
    global API_KEY, HTTP_PROXY, TEST_MODE
    
    retry_count = 0
    last_error = None
    
    # 重试配置
    max_retries = 3  # 增加重试次数
    timeout_base = 45  # 基础超时时间（秒）
    timeout_retry = 60  # 重试时的超时时间（秒）
    
    for attempt in range(max_retries):
        try:
            # 构建 OpenRouter 请求
            openrouter_payload = {
                "model": "openrouter/free",
                "messages": data.get("messages", []),
                "temperature": data.get("temperature", 0.7),
                "max_tokens": data.get("max_tokens", 2000),
                "top_p": data.get("top_p", 1),
            }
            
            # 测试模式或转发到 OpenRouter
            if TEST_MODE:
                # 返回模拟响应
                result = {
                    "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    "created": int(time.time()),
                    "model": "openrouter/free",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "这是一个测试模式的响应。您已成功启动API代理服务！"
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 15,
                        "total_tokens": 25
                    }
                }
                print("[测试模式] 返回模拟响应")
                return result, retry_count
            else:
                # 转发到 OpenRouter
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "LocalAPIProxy",
                }
                
                # 配置代理
                proxies = None
                if HTTP_PROXY:
                    proxies = {
                        "http": HTTP_PROXY,
                        "https": HTTP_PROXY
                    }
                    if attempt == 0:
                        print(f"[代理] 使用代理服务器: {HTTP_PROXY}")
                
                # 根据重试次数调整超时时间
                current_timeout = timeout_retry if attempt > 0 else timeout_base
                attempt_str = f"(尝试 {attempt + 1}/{max_retries})" if attempt > 0 else ""
                print(f"[请求] 发送到 OpenRouter {attempt_str} [超时: {current_timeout}s]")
                
                response = session.post(
                    OPENROUTER_API_URL, 
                    json=openrouter_payload, 
                    headers=headers, 
                    proxies=proxies, 
                    timeout=current_timeout
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"[请求] 成功 {attempt_str}")
                return result, retry_count
        
        except requests.exceptions.Timeout as e:
            last_error = e
            error_msg = f"[请求] 超时 (尝试 {attempt + 1}/{max_retries}): {str(e)}"
            print(error_msg)
            update_daily_counter("timeout")
            
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
            
            # 其他错误不重试
            break
    
    # 所有尝试都失败了
    raise last_error

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
                "last_updated": None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        "retry_eligible": should_retry()
    })

@app.route('/debug', methods=['GET'])
def debug_page():
    """调试页面"""
    # 实时检查调试模式
    debug_enabled = check_debug_mode()
    if not debug_enabled:
        return "Debug mode not enabled", 403
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>API 代理调试面板</title>
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
            /* 测试聊天样式 */
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 API 代理调试面板</h1>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('stats')">统计信息</div>
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
            
            <!-- 测试聊天标签页 -->
            <div id="chat-tab" class="tab-content">
                <h2>💬 AI 聊天测试</h2>
                <div style="margin-bottom: 15px; padding: 10px; background-color: #f0f8ff; border-radius: 5px; font-size: 13px; color: #666;">
                    <strong>📝 参数说明:</strong> max_tokens 控制AI回复的最大长度,默认1000。如果回复被截断,可以增大此值。
                    <br><strong>📍 修改位置:</strong> 后端代码 local_api_proxy.py 第517行 (execute_with_retry函数中的data.get("max_tokens", 2000))
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
                // 隐藏所有标签页内容
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // 显示选中的标签页
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
                
                // 显示用户消息
                addMessage('user', message);
                
                // 清空输入框并禁用按钮
                input.value = '';
                sendBtn.disabled = true;
                sendBtn.textContent = '发送中...';
                
                // 显示加载消息
                const loadingId = 'loading-' + Date.now();
                addMessage('assistant', '<span class="loading">AI 正在思考...</span>', null, false);
                
                const startTime = Date.now();
                
                // 发送请求到API
                fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: 'any-model', // 代理会自动转换为 free 模型
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
                    
                    // 移除加载消息
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
                    
                    // 移除加载消息
                    const loadingMessages = document.querySelectorAll('.message .loading');
                    loadingMessages.forEach(msg => msg.parentElement.remove());
                    
                    addMessage('assistant', `错误: ${error.message}`, latency, true);
                })
                .finally(() => {
                    // 重新启用按钮
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
            
            // 每30秒自动刷新统计
            setInterval(refreshStats, 30000);
            
            // 初始化聊天界面
            document.getElementById('chatMessages').innerHTML = '<div class="message assistant">欢迎使用AI聊天测试！您可以在这里直接测试代理功能。</div>';
        </script>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    # 检测是否为守护进程子进程
    IS_DAEMON_CHILD = os.getenv('DAEMON_CHILD') == '1'
    
    # 端口检查（非守护进程子进程时）
    if not IS_DAEMON_CHILD and is_port_in_use(5000):
        print("=" * 60)
        print("错误：端口 5000 已被占用")
        print("=" * 60)
        print("可能的原因：")
        print("1. 另一个 local_api_proxy.py 实例正在运行")
        print("2. 守护进程正在运行")
        print()
        print("解决方案：")
        print("1. 如果守护进程正在运行，请使用：python daemon.py stop")
        print("2. 查找并停止占用端口的进程：")
        print("   netstat -ano | findstr :5000")
        print("   taskkill /PID <进程ID> /F")
        print("=" * 60)
        sys.exit(1)
    
    print("=" * 60)
    print("本地 API 代理服务启动中...")
    print("=" * 60)
    print("监听地址: http://localhost:5000")
    print("API 端点: http://localhost:5000/v1/chat/completions")
    print("模型列表: http://localhost:5000/v1/models")
    print("健康检查: http://localhost:5000/health")
    print("\n[监控] 启动文件监控...")
    print(f"[监控] 监控文件: {', '.join(WATCHED_FILES)}")
    print("[监控] 文件变化时将自动重新加载配置")
    
    # 检查调试模式
    if DEBUG_MODE:
        print("\n[调试] 调试模式已启用")
        if CACHE_DIR:
            ensure_cache_dir()
        else:
            print("[调试] 未配置 CACHE_DIR，消息不会被保存")
    else:
        print("\n[调试] 调试模式未启用 (创建 DEBUG_MODE.txt 文件以启用)")
    
    print("=" * 60)
    print()
    
    # 启动文件监控
    observer = start_file_watcher()
    
    try:
        app.run(host='localhost', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[关闭] 正在关闭服务...")
    except Exception as e:
        print(f"\n[错误] 服务异常退出: {e}")
        raise
    finally:
        if observer:
            observer.stop()
            observer.join()
        print("[关闭] 服务已关闭")
