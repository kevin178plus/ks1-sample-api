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
WATCHED_FILES = {'.env', 'local_api_proxy.py'}
DEBUG_MODE = False
CACHE_DIR = None
HTTP_PROXY = None

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
            update_daily_counter()
    except Exception as e:
        print(f"[缓存错误] 保存消息失败: {e}")

def update_daily_counter():
    """更新每日调用计数"""
    if not DEBUG_MODE or not CACHE_DIR:
        return
    
    try:
        cache_path = Path(CACHE_DIR)
        today = datetime.now().strftime("%Y%m%d")
        counter_file = cache_path / f"CALLS_{today}.json"
        
        # 读取当前计数
        if counter_file.exists():
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                count = data.get('count', 0)
        else:
            count = 0
        
        # 增加计数
        count += 1
        
        # 写入更新后的计数
        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump({
                'date': today,
                'count': count,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"[计数] 今天已调用 {count} 次")
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
    global API_KEY, DEBUG_MODE, CACHE_DIR, HTTP_PROXY
    # 清除旧的环境变量
    if 'OPENROUTER_API_KEY' in os.environ:
        del os.environ['OPENROUTER_API_KEY']
    if 'CACHE_DIR' in os.environ:
        del os.environ['CACHE_DIR']
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    
    load_env()
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in .env file")
    
    # 更新调试模式和缓存目录
    DEBUG_MODE = check_debug_mode()
    CACHE_DIR = os.getenv("CACHE_DIR")
    HTTP_PROXY = os.getenv("HTTP_PROXY")
    
    if DEBUG_MODE:
        print("[调试] 调试模式已启用")
        if CACHE_DIR:
            ensure_cache_dir()
        else:
            print("[调试] 未配置缓存目录，消息不会被保存")
    
    if HTTP_PROXY:
        print(f"[代理] HTTP 代理已配置: {HTTP_PROXY}")
    
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
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
HTTP_PROXY = os.getenv("HTTP_PROXY")

if not API_KEY and not TEST_MODE:
    raise ValueError("OPENROUTER_API_KEY not found in .env file and TEST_MODE is not enabled")

# 初始化调试模式和缓存目录
DEBUG_MODE = check_debug_mode()
CACHE_DIR = os.getenv("CACHE_DIR")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    global RESTART_FLAG, API_KEY, DEBUG_MODE, CACHE_DIR, HTTP_PROXY
    
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
    
    try:
        data = request.json
        message_id = str(uuid.uuid4())[:8]
        
        # 保存请求消息
        if DEBUG_MODE:
            save_message_cache("REQUEST", message_id, data)
        
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
                print(f"[代理] 使用代理服务器: {HTTP_PROXY}")
            
            response = requests.post(OPENROUTER_API_URL, json=openrouter_payload, headers=headers, proxies=proxies)
            response.raise_for_status()
            
            result = response.json()
        
        # 转换为 OpenAI 兼容格式
        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion",
            "created": result.get("created", 0),
            "model": result.get("model", "openrouter/free"),
            "choices": result.get("choices", []),
            "usage": result.get("usage", {}),
        }
        
        # 保存响应消息
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
    return jsonify({"status": "ok"})

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
                "count": 0,
                "last_updated": None
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            
            <!-- 测试聊天标签页 -->
            <div id="chat-tab" class="tab-content">
                <h2>💬 AI 聊天测试</h2>
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
                        max_tokens: 1000,
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
        observer.stop()
        observer.join()
        print("[关闭] 服务已关闭")
