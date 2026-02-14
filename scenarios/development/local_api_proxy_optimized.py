import os
import json
import sys
import time
import uuid
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# 全局变量
RESTART_FLAG = False
WATCHED_FILES = {'.env', 'local_api_proxy_optimized.py'}
DEBUG_MODE = False
CACHE_DIR = None
MAX_CACHE_FILES = 100  # 最大缓存文件数，防止磁盘空间耗尽

class FileChangeHandler(FileSystemEventHandler):
    """文件监控处理器"""
    def on_modified(self, event):
        global RESTART_FLAG
        if not event.is_directory:
            filename = Path(event.src_path).name
            if filename in WATCHED_FILES:
                print(f"\n[监控] 检测到文件变化: {filename}")
                print("[监控] 将在下一个请求后重启服务...")
                RESTART_FLAG = True

def check_debug_mode():
    """检查调试模式"""
    return Path('DEBUG_MODE.txt').exists()

def cleanup_cache(cache_dir, max_files=MAX_CACHE_FILES):
    """清理缓存文件，防止占用过多磁盘空间"""
    if not cache_dir or not Path(cache_dir).exists():
        return
    
    try:
        cache_path = Path(cache_dir)
        cache_files = list(cache_path.glob("*.json"))
        
        if len(cache_files) > max_files:
            # 按修改时间排序，删除最旧的文件
            cache_files.sort(key=lambda x: x.stat().st_mtime)
            for old_file in cache_files[:-max_files]:
                old_file.unlink()
                print(f"[缓存清理] 删除旧缓存文件: {old_file.name}")
                
    except Exception as e:
        print(f"[缓存错误] 清理失败: {e}")

def save_message_cache(message_type, message_id, data):
    """保存消息缓存"""
    if not DEBUG_MODE or not CACHE_DIR:
        return
    
    try:
        cache_path = Path(CACHE_DIR)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        # 定期清理缓存
        cleanup_cache(CACHE_DIR)
        
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
        print(f"[缓存错误] 保存失败: {e}")

def start_file_watcher():
    """启动文件监控"""
    try:
        observer = Observer()
        observer.schedule(FileChangeHandler(), path='.', recursive=False)
        observer.start()
        return observer
    except Exception as e:
        print(f"[监控] 启动失败: {e}")
        return None

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

# 初始化
load_env()
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    print("⚠️  警告: 未找到OPENROUTER_API_KEY，请配置.env文件")

DEBUG_MODE = check_debug_mode()
CACHE_DIR = os.getenv("CACHE_DIR")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """聊天完成端点"""
    global RESTART_FLAG, API_KEY, DEBUG_MODE, CACHE_DIR
    
    if RESTART_FLAG:
        print("\n[重启] 检测到配置变化，重新加载...")
        try:
            load_env()
            API_KEY = os.getenv("OPENROUTER_API_KEY")
            RESTART_FLAG = False
            print("[重启] 重新加载完成")
        except Exception as e:
            return jsonify({"error": f"配置重载失败: {str(e)}"}), 500
    
    # 检查调试模式
    DEBUG_MODE = check_debug_mode()
    CACHE_DIR = os.getenv("CACHE_DIR")
    
    try:
        data = request.json
        message_id = str(uuid.uuid4())[:8]
        
        # 保存请求缓存
        if DEBUG_MODE:
            save_message_cache("REQUEST", message_id, data)
        
        # 基本验证
        if not data or "messages" not in data:
            return jsonify({"error": "缺少messages字段"}), 400
        
        # 构建请求
        openrouter_payload = {
            "model": "openrouter/free",
            "messages": data.get("messages", []),
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", 2000),
            "top_p": data.get("top_p", 1),
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}" if API_KEY else "Bearer missing-key",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "LocalAPIProxy",
        }
        
        # 添加超时控制
        response = requests.post(
            OPENROUTER_API_URL, 
            json=openrouter_payload, 
            headers=headers,
            timeout=30  # 30秒超时
        )
        response.raise_for_status()
        
        result = response.json()
        
        # 转换响应格式
        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion", 
            "created": result.get("created", int(datetime.now().timestamp())),
            "model": result.get("model", "openrouter/free"),
            "choices": result.get("choices", []),
            "usage": result.get("usage", {}),
        }
        
        # 保存响应缓存
        if DEBUG_MODE:
            save_message_cache("RESPONSE", message_id, response_data)
        
        return jsonify(response_data)
        
    except requests.exceptions.Timeout:
        error_msg = {"error": "请求超时"}
        if DEBUG_MODE:
            save_message_cache("ERROR", message_id, error_msg)
        return jsonify(error_msg), 504
        
    except requests.exceptions.RequestException as e:
        error_msg = {"error": f"OpenRouter API错误: {str(e)}"}
        if DEBUG_MODE:
            save_message_cache("ERROR", message_id, error_msg)
        return jsonify(error_msg), 502
        
    except Exception as e:
        error_msg = {"error": str(e)}
        if DEBUG_MODE:
            save_message_cache("ERROR", message_id, error_msg)
        return jsonify(error_msg), 400

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
    return jsonify({
        "status": "ok",
        "server": "Local API Proxy (优化版)",
        "debug_mode": DEBUG_MODE,
        "cache_enabled": bool(CACHE_DIR),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/debug/stats', methods=['GET'])
def debug_stats():
    """调试统计"""
    if not DEBUG_MODE:
        return jsonify({"error": "调试模式未启用"}), 403
    
    if not CACHE_DIR:
        return jsonify({"error": "未配置缓存目录"}), 400
    
    try:
        cache_path = Path(CACHE_DIR)
        today = datetime.now().strftime("%Y%m%d")
        counter_file = cache_path / f"CALLS_{today}.json"
        
        if counter_file.exists():
            with open(counter_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            return jsonify(stats)
        else:
            return jsonify({
                "date": today,
                "count": 0,
                "last_updated": None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug', methods=['GET'])
def debug_page():
    """调试页面"""
    if not check_debug_mode():
        return "调试模式未启用", 403
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>API 代理调试面板 (优化版)</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background-color: #f5f5f5; }
            .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
            .stats { background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .stat-item { margin: 10px 0; font-size: 16px; }
            .stat-label { font-weight: bold; color: #333; }
            .stat-value { color: #007bff; font-size: 24px; font-weight: bold; }
            .refresh-btn { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
            .refresh-btn:hover { background-color: #0056b3; }
            .timestamp { color: #666; font-size: 12px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 API 代理调试面板 (优化版)</h1>
            
            <div class="stats">
                <div class="stat-item">
                    <span class="stat-label">今天已调用:</span>
                    <span class="stat-value" id="callCount">-</span>
                    <span> 次</span>
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
            
            <button class="refresh-btn" onclick="refreshStats()">刷新统计</button>
        </div>
        
        <script>
            function refreshStats() {
                fetch('/debug/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('callCount').textContent = data.count || 0;
                        document.getElementById('date').textContent = data.date || '-';
                        document.getElementById('lastUpdated').textContent = data.last_updated ? new Date(data.last_updated).toLocaleString() : '-';
                        document.getElementById('refreshTime').textContent = '刷新于: ' + new Date().toLocaleTimeString();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        document.getElementById('callCount').textContent = '错误';
                    });
            }
            
            refreshStats();
            setInterval(refreshStats, 5000);
        </script>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    print("=" * 60)
    print("本地 API 代理服务启动中... (优化版)")
    print("=" * 60)
    print("监听地址: http://localhost:5000")
    print("改进特性:")
    print("  ✓ 添加超时控制 (30秒)")
    print("  ✓ 缓存文件数量限制 (防止磁盘耗尽)")
    print("  ✓ 更好的错误处理")
    print("  ✓ 改进的调试模式")
    print()
    
    # 启动文件监控
    observer = start_file_watcher()
    
    # 检查调试模式
    if DEBUG_MODE:
        print("[调试] 调试模式已启用")
        if CACHE_DIR:
            ensure_cache_dir()
            print(f"[调试] 缓存目录: {CACHE_DIR}")
        else:
            print("[调试] 未配置缓存目录")
    else:
        print("[调试] 调试模式未启用 (创建 DEBUG_MODE.txt 启用)")
    
    print("=" * 60)
    
    try:
        app.run(host='localhost', port=5000, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[关闭] 正在关闭服务...")
        if observer:
            observer.stop()
            observer.join()
        print("[关闭] 服务已关闭")