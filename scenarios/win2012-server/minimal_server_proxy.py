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