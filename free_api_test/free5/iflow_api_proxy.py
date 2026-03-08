"""
基于 iflow_sdk 的 API 代理服务
提供 OpenAI API 兼容的接口
"""

import os
import json
import sys
import time
import uuid
import threading
import asyncio
import socket
from pathlib import Path
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 导入 iflow_sdk
try:
    from iflow_sdk import query as iflow_query
except ImportError:
    print("错误: 未找到 iflow_sdk，请先安装: pip install iflow-sdk")
    sys.exit(1)

app = Flask(__name__)

# 全局变量
RESTART_FLAG = False
WATCHED_FILES = {'.env', 'iflow_api_proxy.py'}
DEBUG_MODE = False
CACHE_DIR = None

# 并发控制相关
MAX_CONCURRENT_REQUESTS = 5
ACTIVE_REQUESTS = 0
ACTIVE_LOCK = threading.Lock()

# 调用历史记录
CALL_HISTORY = deque(maxlen=10)
HISTORY_LOCK = threading.Lock()

# 错误类型
ERROR_TYPES = {
    "NONE": "none",
    "TIMEOUT": "timeout",
    "API_ERROR": "api_error",
    "CONCURRENT_LIMIT": "concurrent_limit",
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

def start_file_watcher():
    """启动文件监控"""
    observer = Observer()
    observer.schedule(FileChangeHandler(), path='.', recursive=False)
    observer.start()
    return observer

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

DEBUG_MODE = check_debug_mode()
CACHE_DIR = os.getenv("CACHE_DIR")
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

def execute_with_iflow(data, message_id):
    """使用 iflow_sdk 执行请求"""
    global DEBUG_MODE, CACHE_DIR

    try:
        # 从请求中提取消息
        messages = data.get("messages", [])
        if not messages:
            raise ValueError("No messages provided")

        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        if not user_message:
            raise ValueError("No user message found")

        # 使用 iflow_sdk 查询
        print(f"[iflow] 发送查询: {user_message[:50]}...")

        # 创建事件循环执行异步查询
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response_text = loop.run_until_complete(iflow_query(user_message))
        finally:
            loop.close()

        # 构建 OpenAI 兼容格式的响应
        result = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "created": int(time.time()),
            "model": "iflow",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_message),
                "completion_tokens": len(response_text),
                "total_tokens": len(user_message) + len(response_text)
            }
        }

        print(f"[iflow] 收到响应: {response_text[:50]}...")
        return result, 0  # 返回结果和重试次数

    except Exception as e:
        print(f"[iflow] 查询失败: {e}")
        raise

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    global RESTART_FLAG, DEBUG_MODE, CACHE_DIR, ACTIVE_REQUESTS, MAX_CONCURRENT_REQUESTS

    # 检查是否需要重启
    if RESTART_FLAG:
        print("\n[重启] 检测到配置变化，重新加载...")
        try:
            load_env()
            RESTART_FLAG = False
            print("[重启] 重新加载完成")
        except Exception as e:
            print(f"[错误] 重新加载失败: {e}")
            return jsonify({"error": f"Configuration reload failed: {str(e)}"}), 500

    DEBUG_MODE = check_debug_mode()
    CACHE_DIR = os.getenv("CACHE_DIR")

    # 检查并发限制（带超时）
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

        result, retry_count = execute_with_iflow(data, message_id)

        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion",
            "created": result.get("created", 0),
            "model": result.get("model", "iflow"),
            "choices": result.get("choices", []),
            "usage": result.get("usage", {}),
        }

        with HISTORY_LOCK:
            CALL_HISTORY.append({"success": True, "timestamp": datetime.now()})

        if DEBUG_MODE:
            response_data["_retry_count"] = retry_count
            save_message_cache("RESPONSE", message_id, response_data)

        return jsonify(response_data)

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
        return jsonify(error_response), 500
    finally:
        with ACTIVE_LOCK:
            ACTIVE_REQUESTS -= 1
        print(f"[并发] 请求完成 (当前: {ACTIVE_REQUESTS}/{MAX_CONCURRENT_REQUESTS})")

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出可用模型"""
    return jsonify({
        "object": "list",
        "data": [{
            "id": "iflow",
            "object": "model",
            "owned_by": "iflow",
            "permission": []
        }]
    })

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

@app.route('/debug/stats', methods=['GET'])
def debug_stats():
    """获取调试统计信息"""
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
        "last_error": last_error
    })

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出可用模型（OpenAI API 兼容）"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": "iflow-model",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "iflow"
            }
        ]
    })

if __name__ == '__main__':
    PORT = 5005  # free5 专用端口
    if is_port_in_use(PORT):
        print("=" * 60)
        print(f"错误：端口 {PORT} 已被占用")
        print("=" * 60)
        print("解决方案：")
        print(f"1. 查找并停止占用端口的进程：")
        print(f"   netstat -ano | findstr :{PORT}")
        print("   taskkill /PID <进程ID> /F")
        print("=" * 60)
        sys.exit(1)

    print("=" * 60)
    print("iflow API 代理服务启动中...")
    print("=" * 60)
    print(f"监听地址: http://localhost:{PORT}")
    print(f"API 端点: http://localhost:{PORT}/v1/chat/completions")
    print(f"模型列表: http://localhost:{PORT}/v1/models")
    print(f"健康检查: http://localhost:{PORT}/health")
    print("\n[监控] 启动文件监控...")
    print(f"[监控] 监控文件: {', '.join(WATCHED_FILES)}")
    print("[监控] 文件变化时将自动重新加载配置")

    if DEBUG_MODE:
        print("\n[调试] 调试模式已启用")
        if CACHE_DIR:
            cache_path = Path(CACHE_DIR)
            cache_path.mkdir(parents=True, exist_ok=True)
            print(f"[调试] 缓存目录: {CACHE_DIR}")
        else:
            print("[调试] 未配置 CACHE_DIR，消息不会被保存")
    else:
        print("\n[调试] 调试模式未启用 (创建 DEBUG_MODE.txt 文件以启用)")

    print("=" * 60)
    print()

    # 启动文件监控
    observer = start_file_watcher()

    try:
        app.run(host='localhost', port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[关闭] 正在关闭服务...")
    except Exception as e:
        print(f"\n[错误] 服务异常退出: {e}")
        raise
    finally:
        if observer:
            observer.stop()
            observer.join()
