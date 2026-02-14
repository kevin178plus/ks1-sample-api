import os
import json
import sys
import time
import uuid
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from functools import wraps
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)

# 安全配置
SECURITY_CONFIG = {
    'allowed_ips': [],
    'secret_token': None,
    'enable_rate_limit': False,
    'max_requests_per_hour': 100,
    'rate_limit_cache': {},
    'request_logs': []
}

# 全局变量
RESTART_FLAG = False
WATCHED_FILES = {'.env', '.env.production', 'secure_api_proxy.py'}
DEBUG_MODE = False
CACHE_DIR = None

class SecurityMiddleware:
    """安全中间件"""
    
    @staticmethod
    def check_ip_whitelist():
        """检查IP白名单"""
        client_ip = request.remote_addr
        allowed_ips = SECURITY_CONFIG['allowed_ips']
        
        if not allowed_ips:
            return True  # 如果没有配置白名单，允许所有IP
            
        return client_ip in allowed_ips
    
    @staticmethod
    def check_token():
        """检查访问令牌"""
        token = request.headers.get('Authorization')
        if not token:
            return False
        
        # 移除 "Bearer " 前缀
        if token.startswith('Bearer '):
            token = token[7:]
        
        secret_token = SECURITY_CONFIG['secret_token']
        if not secret_token:
            return True  # 如果没有配置token，跳过验证
        
        # 简单的token验证（实际项目中应使用JWT等）
        return token == secret_token
    
    @staticmethod
    def check_rate_limit():
        """检查请求频率限制"""
        if not SECURITY_CONFIG['enable_rate_limit']:
            return True
        
        client_ip = request.remote_addr
        now = datetime.now()
        cache = SECURITY_CONFIG['rate_limit_cache']
        
        # 清理过期记录
        expired_keys = [k for k, v in cache.items() 
                       if now - v['first_request'] > timedelta(hours=1)]
        for k in expired_keys:
            del cache[k]
        
        # 检查当前IP的请求次数
        if client_ip not in cache:
            cache[client_ip] = {
                'count': 1,
                'first_request': now
            }
            return True
        
        if cache[client_ip]['count'] >= SECURITY_CONFIG['max_requests_per_hour']:
            return False
        
        cache[client_ip]['count'] += 1
        return True

def require_auth(f):
    """身份验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查IP白名单
        if not SecurityMiddleware.check_ip_whitelist():
            app.logger.warning(f'Unauthorized IP access attempt: {request.remote_addr}')
            return jsonify({"error": "IP not allowed"}), 403
        
        # 检查访问令牌
        if not SecurityMiddleware.check_token():
            app.logger.warning(f'Invalid token attempt from: {request.remote_addr}')
            return jsonify({"error": "Invalid token"}), 401
        
        # 检查频率限制
        if not SecurityMiddleware.check_rate_limit():
            app.logger.warning(f'Rate limit exceeded for: {request.remote_addr}')
            return jsonify({"error": "Rate limit exceeded"}), 429
        
        return f(*args, **kwargs)
    return decorated_function

def load_security_config():
    """加载安全配置"""
    env_file = ".env.production" if os.path.exists(".env.production") else ".env"
    
    # 加载环境变量
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    # 配置安全参数
    allowed_ips_str = os.getenv("ALLOWED_IPS", "")
    if allowed_ips_str:
        SECURITY_CONFIG['allowed_ips'] = [ip.strip() for ip in allowed_ips_str.split(",")]
    
    SECURITY_CONFIG['secret_token'] = os.getenv("SECRET_TOKEN")
    
    if os.getenv("ENABLE_RATE_LIMIT", "").lower() == "true":
        SECURITY_CONFIG['enable_rate_limit'] = True
        SECURITY_CONFIG['max_requests_per_hour'] = int(os.getenv("MAX_REQUESTS_PER_HOUR", "100"))

# 文件监控
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global RESTART_FLAG
        if not event.is_directory:
            filename = Path(event.src_path).name
            if filename in WATCHED_FILES:
                app.logger.info(f'Configuration file changed: {filename}')
                RESTART_FLAG = True

def check_debug_mode():
    return Path('DEBUG_MODE.txt').exists()

def save_message_cache(message_type, message_id, data):
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
                'client_ip': request.remote_addr,
                'data': data
            }, f, indent=2, ensure_ascii=False)
        
        app.logger.debug(f'Cached {message_type} message: {filename}')
        
    except Exception as e:
        app.logger.error(f'Cache save failed: {e}')

def reload_config():
    global API_KEY, DEBUG_MODE, CACHE_DIR
    try:
        load_security_config()
        API_KEY = os.getenv("OPENROUTER_API_KEY")
        if not API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found")
        
        DEBUG_MODE = check_debug_mode()
        CACHE_DIR = os.getenv("CACHE_DIR")
        
        app.logger.info('Configuration reloaded successfully')
        RESTART_FLAG = False
        
    except Exception as e:
        app.logger.error(f'Configuration reload failed: {e}')
        raise

# 初始化配置
load_security_config()
reload_config()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/v1/chat/completions', methods=['POST'])
@require_auth
def chat_completions():
    global RESTART_FLAG, API_KEY, DEBUG_MODE, CACHE_DIR
    
    if RESTART_FLAG:
        try:
            reload_config()
        except Exception as e:
            return jsonify({"error": f"Configuration reload failed: {str(e)}"}), 500
    
    try:
        data = request.json
        message_id = str(uuid.uuid4())[:8]
        
        # 记录请求日志（不包含敏感内容）
        app.logger.info(f'Chat completion request from {request.remote_addr}, message_id: {message_id}')
        
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
            "HTTP-Referer": os.getenv("REFERER_URL", "http://localhost:5000"),
            "X-Title": "SecureLocalAPIProxy",
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
        
        app.logger.info(f'Chat completion completed for message_id: {message_id}')
        return jsonify(response_data)
    
    except requests.exceptions.Timeout:
        error_msg = "Request timeout"
        app.logger.error(f'Timeout error for message_id: {message_id}')
        return jsonify({"error": error_msg}), 504
    except requests.exceptions.RequestException as e:
        error_msg = f"OpenRouter API error: {str(e)}"
        app.logger.error(f'API error for message_id: {message_id}: {e}')
        return jsonify({"error": error_msg}), 502
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f'Unexpected error for message_id: {message_id}: {e}')
        return jsonify({"error": error_msg}), 400

@app.route('/v1/models', methods=['GET'])
@require_auth
def list_models():
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
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/admin/stats', methods=['GET'])
@require_auth
def admin_stats():
    """管理统计信息"""
    try:
        stats = {
            "security_config": {
                "ip_whitelist_enabled": len(SECURITY_CONFIG['allowed_ips']) > 0,
                "token_auth_enabled": SECURITY_CONFIG['secret_token'] is not None,
                "rate_limit_enabled": SECURITY_CONFIG['enable_rate_limit'],
                "max_requests_per_hour": SECURITY_CONFIG['max_requests_per_hour']
            },
            "current_rate_limits": {
                ip: {"count": data["count"], "first_request": data["first_request"].isoformat()}
                for ip, data in SECURITY_CONFIG['rate_limit_cache'].items()
            },
            "debug_mode": DEBUG_MODE,
            "cache_configured": CACHE_DIR is not None
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 配置日志
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('api_proxy.log'),
            logging.StreamHandler()
        ]
    )
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    
    print("=" * 60)
    print("安全版 API 代理服务启动中...")
    print("=" * 60)
    print(f"监听地址: http://{host}:{port}")
    print("安全配置:")
    print(f"  IP白名单: {SECURITY_CONFIG['allowed_ips'] if SECURITY_CONFIG['allowed_ips'] else '未配置'}")
    print(f"  Token认证: {'已启用' if SECURITY_CONFIG['secret_token'] else '未启用'}")
    print(f"  频率限制: {'已启用' if SECURITY_CONFIG['enable_rate_limit'] else '未启用'}")
    print(f"  调试模式: {'已启用' if DEBUG_MODE else '已禁用'}")
    print("=" * 60)
    
    # 启动文件监控
    observer = Observer()
    observer.schedule(FileChangeHandler(), path='.', recursive=False)
    observer.start()
    
    try:
        app.run(host=host, port=port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n服务关闭中...")
        observer.stop()
        observer.join()
        print("服务已关闭")