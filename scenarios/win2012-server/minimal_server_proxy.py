# 最小化服务器代理 - 适配 Windows Server 2012 R2
# 优化内存使用，移除不必要的功能

import os
import json
import sys
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 简化配置 - 移除文件监控以节省内存
API_KEY = None

def load_env():
    """加载环境变量"""
    global API_KEY
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found in .env file")

# 初始化
load_env()
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """聊天完成端点 - 最小化实现"""
    try:
        data = request.json
        
        # 基本验证
        if not data or "messages" not in data:
            return jsonify({"error": "Missing messages field"}), 400
        
        # 构建 OpenRouter 请求
        openrouter_payload = {
            "model": "openrouter/free",
            "messages": data.get("messages", []),
            "temperature": data.get("temperature", 0.7),
            "max_tokens": min(data.get("max_tokens", 1000), 1500),  # 限制token节省内存
            "top_p": data.get("top_p", 1),
        }
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://your-server.com:5000",
            "X-Title": "MinimalAPIProxy",
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
        
        # 转换为 OpenAI 兼容格式
        response_data = {
            "id": result.get("id", ""),
            "object": "chat.completion",
            "created": result.get("created", int(datetime.now().timestamp())),
            "model": result.get("model", "openrouter/free"),
            "choices": result.get("choices", []),
            "usage": result.get("usage", {}),
        }
        
        return jsonify(response_data)
    
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 400

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
    """健康检查 - 最小化"""
    return jsonify({
        "status": "ok",
        "server": "Minimal API Proxy",
        "memory": "optimized"
    })

@app.route('/stats', methods=['GET'])
def stats():
    """基本统计信息"""
    return jsonify({
        "server_info": "Windows Server 2012 R2 Compatible",
        "version": "1.0-minimal",
        "uptime": "running"
    })

@app.route('/debug', methods=['GET'])
def debug_page():
    """简化版调试页面 - 最小化内存占用"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>API 代理调试面板</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
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
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .status-ok {
            background-color: #d4edda;
            color: #155724;
        }
        .status-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        textarea {
            width: 100%;
            height: 100px;
            margin-bottom: 10px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: monospace;
        }
        button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .response {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>API 代理调试面板</h1>
        <div class="status status-ok">
            <strong>服务状态:</strong> 运行中
        </div>
        <div class="status status-warning">
            <strong>版本:</strong> 最小化版本 (Windows Server 2012 R2)
        </div>
    </div>

    <div class="container">
        <h2>API 测试</h2>
        <p>输入消息内容测试 API:</p>
        <textarea id="message" placeholder="输入你的消息...">你好，请介绍一下自己。</textarea>
        <button onclick="testAPI()">发送请求</button>
        <div id="response" class="response" style="display:none;"></div>
    </div>

    <div class="container">
        <h2>API 端点</h2>
        <ul>
            <li><strong>聊天完成:</strong> POST /v1/chat/completions</li>
            <li><strong>模型列表:</strong> GET /v1/models</li>
            <li><strong>健康检查:</strong> GET /health</li>
            <li><strong>统计信息:</strong> GET /stats</li>
        </ul>
    </div>

    <script>
        async function testAPI() {
            const message = document.getElementById('message').value;
            const responseDiv = document.getElementById('response');
            
            responseDiv.style.display = 'block';
            responseDiv.textContent = '发送中...';
            
            try {
                const response = await fetch('/v1/chat/completions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        model: 'openrouter/free',
                        messages: [
                            {
                                role: 'user',
                                content: message
                            }
                        ],
                        max_tokens: 1000
                    })
                });
                
                const data = await response.json();
                
                if (data.choices && data.choices.length > 0) {
                    responseDiv.textContent = '回复: ' + data.choices[0].message.content;
                } else if (data.error) {
                    responseDiv.textContent = '错误: ' + data.error;
                } else {
                    responseDiv.textContent = '未知响应: ' + JSON.stringify(data, null, 2);
                }
            } catch (error) {
                responseDiv.textContent = '请求失败: ' + error.message;
            }
        }
    </script>
</body>
</html>
    """
    return html

if __name__ == '__main__':
    print("=" * 50)
    print("最小化 API 代理服务")
    print("适配 Windows Server 2012 R2")
    print("=" * 50)
    print("监听地址: http://0.0.0.0:5000")
    print("内存优化: 已启用")
    print("功能简化: 核心功能保留")
    print("=" * 50)
    
    try:
        # 使用简单配置，适合旧系统
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=False, 
            threaded=True,  # 多线程处理
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n服务已关闭")