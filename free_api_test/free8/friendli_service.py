#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Friendli.ai 独立服务
提供带权重模型选择的 OpenAI API 兼容接口
"""

import os
import sys
import json
import time
import uuid
import random
import asyncio
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# 添加父目录到路径以导入配置
sys.path.insert(0, str(Path(__file__).parent.parent))
from free8.config import API_KEY, BASE_URL, AVAILABLE_MODELS, MAX_TOKENS

app = Flask(__name__)

# 配置
PORT = 5008
FRIENDLI_BASE_URL = BASE_URL
FRIENDLI_API_KEY = API_KEY

# 会话
session = requests.Session()

def get_weight_distribution():
    """
    计算模型权重分布（按列表顺序递减）
    Returns:
        dict: {model_name: weight}
    """
    n = len(AVAILABLE_MODELS)
    if n == 0:
        return {}
    # 权重从 n 递减到 1
    weights = list(range(n, 0, -1))
    return dict(zip(AVAILABLE_MODELS, weights))

def select_model_by_weight():
    """
    根据权重随机选择一个模型
    Returns:
        str: 选中的模型名称
    """
    weights = get_weight_distribution()
    if not weights:
        raise ValueError("No models available")

    # 计算总权重
    total_weight = sum(weights.values())

    # 随机选择
    r = random.randint(1, total_weight)
    cumulative = 0

    for model, weight in weights.items():
        cumulative += weight
        if r <= cumulative:
            return model

    # 兜底返回权重最高的（第一个）
    return AVAILABLE_MODELS[0]

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "service": "friendli", "models": len(AVAILABLE_MODELS)})

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出可用模型（OpenAI API 兼容）"""
    return jsonify({
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "friendli"
            }
            for model in AVAILABLE_MODELS
        ]
    })

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """聊天完成端点（OpenAI API 兼容）"""
    try:
        data = request.get_json()

        # 检查是否有模型选择
        model = data.get("model")
        if model and model in AVAILABLE_MODELS:
            # 使用指定的模型
            selected_model = model
        else:
            # 使用权重随机选择
            selected_model = select_model_by_weight()

        # 构建 Friendli API 请求
        url = f"{FRIENDLI_BASE_URL}/chat/completions"
        headers = {
            'Authorization': f'Bearer {FRIENDLI_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            "model": selected_model,
            "messages": data.get("messages", []),
            "temperature": data.get("temperature", 0.7),
            "max_tokens": data.get("max_tokens", MAX_TOKENS),
            "top_p": data.get("top_p", 1.0),
        }

        # 发送请求
        response = session.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        result = response.json()

        # 添加调试信息
        result["_debug"] = {
            "selected_model": selected_model,
            "weight_distribution": get_weight_distribution(),
            "timestamp": datetime.now().isoformat()
        }

        return jsonify(result)

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": {
                "message": str(e),
                "type": "api_error",
                "code": "api_error"
            }
        }), 500
    except Exception as e:
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_error",
                "code": "internal_error"
            }
        }), 500

@app.route('/v1/stats', methods=['GET'])
def stats():
    """获取统计信息"""
    return jsonify({
        "service": "friendli",
        "models": {
            "count": len(AVAILABLE_MODELS),
            "list": AVAILABLE_MODELS,
            "weight_distribution": get_weight_distribution()
        }
    })

def is_port_in_use(port):
    """检查端口是否被占用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

if __name__ == '__main__':
    if is_port_in_use(PORT):
        print("=" * 60)
        print(f"错误：端口 {PORT} 已被占用")
        print("=" * 60)
        print(f"解决方案：")
        print(f"   netstat -ano | findstr :{PORT}")
        print("   taskkill /PID <进程ID> /F")
        print("=" * 60)
        sys.exit(1)

    print("=" * 60)
    print("Friendli.ai 服务启动中...")
    print("=" * 60)
    print(f"监听地址: http://localhost:{PORT}")
    print(f"API 端点: http://localhost:{PORT}/v1/chat/completions")
    print(f"模型列表: http://localhost:{PORT}/v1/models")
    print(f"统计信息: http://localhost:{PORT}/v1/stats")
    print(f"健康检查: http://localhost:{PORT}/health")
    print()
    print(f"可用模型 ({len(AVAILABLE_MODELS)}):")
    weights = get_weight_distribution()
    for i, model in enumerate(AVAILABLE_MODELS):
        weight = weights.get(model, 0)
        print(f"  {i+1}. {model} (权重: {weight})")
    print("=" * 60)

    try:
        app.run(host='localhost', port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n[关闭] 正在关闭服务...")
    except Exception as e:
        print(f"\n[错误] 服务异常退出: {e}")
        raise