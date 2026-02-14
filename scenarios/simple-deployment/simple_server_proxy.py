# 简化版服务器API代理 - 适合云服务器内网使用
# 只需要把原文件的最后一行改一下就行

import os
import json
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# 全局变量用于重启控制
RESTART_FLAG = False
WATCHED_FILES = {'.env', 'simple_server_proxy.py'}
DEBUG_MODE = False
CACHE_DIR = None

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
    global API_KEY, DEBUG_MODE, CACHE_DIR
    
    if 'OPENROUTER_API_KEY' in os.environ:
        del os.environ['OPENROUTER_API_KEY']
    if 'CACHE_DIR' in os.environ:
        del os.environ['CACHE_DIR']
    
    load_env()
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in .env file")
    
    DEBUG_MODE = check_debug_mode()
    CACHE_DIR = os.getenv("CACHE_DIR")
    
    if DEBUG_MODE:
        print("[调试] 调试模式已启用")
        if CACHE_DIR:
            ensure_cache_dir()
        else:
            print("[调试] 未配置缓存目录，消息不会被保存")
    
    print("[重载] 环境变量已重新加载")

# 从 .env 文件读取 API Key
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
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")

DEBUG_MODE = check_debug_mode()
CACHE_DIR = os.getenv("CACHE_DIR")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    global RESTART_FLAG, API_KEY, DEBUG_MODE, CACHE_DIR
    
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
    
    try:
        data = request.json
        message_id = str(uuid.uuid4())[:8]
        
        if DEBUG_MODE:
            save_message_cache("REQUEST", message_id, data)
        
        openrouter_payload = {
            "model": "openrouter/free",
            "messages": data.get("messages", []),
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 2000),
            "top_p": data.get("top_p", 1),
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://your-server.com:5000",
            "X-Title": "SimpleAPIProxy",
        }
        
        response = requests.post(OPENROUTER_API_URL, json=openrouter_payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion",
            "created": result.get("created", 0),
            "model": result.get("model", "openrouter/free"),
            "choices": result.get("choices", []),
            "usage": result.get("usage", {}),
        }
        
        if DEBUG_MODE:
            save_message_cache("RESPONSE", message_id, response_data)
        
        return jsonify(response_data)
    
    except requests.exceptions.RequestException as e:
        error_response = {"error": f"OpenRouter API error: {str(e)}"}
        if DEBUG_MODE:
            save_message_cache("ERROR", str(uuid.uuid4())[:8], error_response)
        return jsonify(error_response), 502
    except Exception as e:
        error_response = {"error": str(e)}
        if DEBUG_MODE:
            save_message_cache("ERROR", str(uuid.uuid4())[:8], error_response)
        return jsonify(error_response), 400

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
    return jsonify({"status": "ok", "server": "Simple API Proxy"})

if __name__ == '__main__':
    print("=" * 60)
    print("简化版 API 代理服务启动中...")
    print("=" * 60)
    print("监听地址: http://0.0.0.0:5000  # 可被其他服务器访问")
    print("API 端点: http://0.0.0.0:5000/v1/chat/completions")
    print("健康检查: http://0.0.0.0:5000/health")
    print("\n[监控] 启动文件监控...")
    print(f"[监控] 监控文件: {', '.join(WATCHED_FILES)}")
    
    if DEBUG_MODE:
        print("\n[调试] 调试模式已启用")
        if CACHE_DIR:
            ensure_cache_dir()
        else:
            print("[调试] 未配置 CACHE_DIR，消息不会被保存")
    
    print("=" * 60)
    print()
    
    observer = start_file_watcher()
    
    try:
        # 🔥 关键修改：从 localhost 改为 0.0.0.0，允许外网访问
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[关闭] 正在关闭服务...")
        observer.stop()
        observer.join()
        print("[关闭] 服务已关闭")