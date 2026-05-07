"""
多Free API代理服务 - 优化版本
自动检测、测试和轮换使用多个Free API
"""

import os
import sys
import json
import time
import threading
import socket
import requests
import importlib.util
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify, render_template
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 导入本地模块
from config import get_config
from app_state import AppState
from errors import ErrorType, APIError, TimeoutError, UpstreamError, ConcurrentLimitError, NoAvailableAPIError, FormatError

# 初始化配置和状态
config = get_config()
app_state = AppState(config)

def update_call_stats(success=True, is_timeout=False):
    """更新调用统计"""
    cache_dir = config.CACHE_DIR or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
    if not cache_dir:
        return
    
    try:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y%m%d")
        counter_file = cache_path / f"CALLS_{today}.json"
        
        if counter_file.exists():
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"total": 0, "success": 0, "failed": 0, "timeout": 0, "retry": 0}
        
        data["total"] = data.get("total", 0) + 1
        if is_timeout:
            data["timeout"] = data.get("timeout", 0) + 1
        elif success:
            data["success"] = data.get("success", 0) + 1
        else:
            data["failed"] = data.get("failed", 0) + 1
        data["date"] = today
        data["last_updated"] = datetime.now().isoformat()
        
        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[统计] 更新失败: {e}")

# 创建 Flask 应用
app = Flask(__name__, template_folder='templates', static_folder='static')

# 配置 requests 会话
session = requests.Session()

class FileChangeHandler(FileSystemEventHandler):
    """监控文件变化"""
    def on_modified(self, event):
        if not event.is_directory:
            filename = Path(event.src_path).name
            if filename in config.WATCHED_FILES:
                print(f"\n[监控] 检测到文件变化: {filename}")
                print("[监控] 将在下一个请求后重启服务...")
                app_state.restart_flag = True

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except socket.error:
            return True

def load_env():
    """加载环境变量"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

def load_api_configs():
    """从free_api_test目录自动加载API配置"""
    script_dir = Path(__file__).parent
    free_api_dir = script_dir.parent / "free_api_test"

    print(f"[调试] 脚本目录: {script_dir}")
    print(f"[调试] API目录: {free_api_dir}")

    if not free_api_dir.exists():
        print(f"[警告] 未找到 free_api_test 目录: {free_api_dir}")
        return

    api_dirs = list(free_api_dir.glob("free*"))
    print(f"[调试] 找到 {len(api_dirs)} 个 API 目录: {[d.name for d in api_dirs]}")

    for api_dir in sorted(api_dirs):
        api_name = api_dir.name
        config_file = api_dir / "config.py"

        if not config_file.exists():
            print(f"[跳过] {api_name}: 未找到 config.py")
            continue

        try:
            spec = importlib.util.spec_from_file_location(
                f"config_{api_name}",
                str(config_file)
            )
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)

            api_key = getattr(config_module, "API_KEY", None)
            base_url = getattr(config_module, "BASE_URL", None)
            model_name = getattr(config_module, "MODEL_NAME", None)
            use_proxy = getattr(config_module, "USE_PROXY", False)
            use_sdk = getattr(config_module, "USE_SDK", False)
            available_models = getattr(config_module, "AVAILABLE_MODELS", [])
            max_tokens = getattr(config_module, "MAX_TOKENS", config.DEFAULT_MAX_TOKENS)
            default_weight = getattr(config_module, "DEFAULT_WEIGHT", 10)
            endpoint = getattr(config_module, "ENDPOINT", "/v1/chat/completions")
            response_format = getattr(config_module, "RESPONSE_FORMAT", {
                "content_fields": ["content"],
                "merge_fields": False,
                "use_reasoning_as_fallback": False
            })

            if not base_url or not model_name:
                print(f"[跳过] {api_name}: 配置不完整")
                continue

            env_key = f"{api_name.upper()}_API_KEY"
            env_api_key = os.getenv(env_key)
            if not env_api_key:
                print(f"[跳过] {api_name}: 环境变量 {env_key} 未配置")
                continue

            api_key = env_api_key

            if api_name == "free1":
                use_proxy = True
            elif api_name == "free5":
                use_sdk = True

            api_config = {
                "name": api_name,
                "api_key": api_key,
                "base_url": base_url,
                "model": model_name,
                "available_models": available_models,
                "max_tokens": max_tokens,
                "default_weight": default_weight,
                "use_proxy": use_proxy,
                "endpoint": endpoint,
                "response_format": response_format,
                "available": False,
                "last_test_time": None,
                "last_test_result": None,
                "success_count": 0,
                "failure_count": 0,
                "consecutive_failures": 0
            }

            if use_sdk:
                api_config["use_sdk"] = True

            # 验证API配置
            is_valid, error_msg = validate_api_config(api_name, api_config)
            if not is_valid:
                print(f"[跳过] {api_name}: 配置验证失败 - {error_msg}")
                continue

            app_state.add_api(api_name, api_config)
            print(f"[加载] {api_name}: {model_name} @ {base_url}")

        except Exception as e:
            print(f"[错误] 加载 {api_name} 配置失败: {e}")

    print(f"[配置] 已加载 {len(app_state.get_all_apis())} 个API配置")
    
    # 启动前验证
    validate_all_apis_before_startup()
    
    init_default_weights()


def validate_all_apis_before_startup():
    """启动前验证所有API配置"""
    print("\n[配置验证] 开始验证所有API配置...")
    
    all_apis = app_state.get_all_apis()
    valid_count = 0
    invalid_count = 0
    validation_results = []
    
    for api_name, api_config in all_apis.items():
        is_valid, error_msg = validate_api_config(api_name, api_config)
        
        if is_valid:
            valid_count += 1
            # 检查API_KEY是否为空
            if not api_config.get("api_key"):
                error_msg = "API_KEY未配置"
                is_valid = False
        else:
            invalid_count += 1
        
        validation_results.append({
            "api_name": api_name,
            "is_valid": is_valid,
            "error": error_msg
        })
        
        status = "✅" if is_valid else "❌"
        print(f"[配置验证] {status} {api_name}: {error_msg if error_msg else '配置正确'}")
    
    print(f"\n[配置验证] 验证完成: {valid_count} 个有效, {invalid_count} 个无效")
    if invalid_count > 0:
        print("[警告] 部分API配置无效，这些API将不会被加载")
    print()

def init_default_weights():
    """初始化默认权重"""
    weights = {}
    for api_name, api_config in app_state.get_all_apis().items():
        weights[api_name] = api_config.get("default_weight", 10)
    app_state.init_weights(weights)
    print(f"[权重] 默认权重已初始化: {weights}")

def validate_api_config(api_name: str, api_config: Dict) -> tuple[bool, str]:
    """验证API配置的完整性
    
    Returns:
        (是否有效, 错误信息)
    """
    errors = []
    
    # 检查必要字段
    required_fields = ["base_url", "model", "api_key"]
    for field in required_fields:
        if not api_config.get(field):
            errors.append(f"缺少必要字段: {field}")
    
    # 检查base_url格式
    base_url = api_config.get("base_url", "")
    if base_url:
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            errors.append(f"base_url格式不正确: {base_url}")
    
    # 检查model是否为空
    model = api_config.get("model", "")
    if not model:
        errors.append("model不能为空")
    
    if errors:
        return False, "; ".join(errors)
    return True, ""

def test_api_startup(api_name):
    """启动时测试API是否可用
    
    Returns:
        True if successful, False otherwise
    """
    api_config = app_state.get_api(api_name)
    if not api_config:
        print(f"[启动测试] {api_name} 配置不存在")
        return False

    api_key = api_config["api_key"]
    base_url = api_config["base_url"]
    model = api_config.get("model", "gpt-3.5-turbo")
    use_proxy = api_config.get("use_proxy", False)

    print(f"[启动测试] 测试 {api_name} (模型: {model}, 代理: {use_proxy})...")

    if api_name in ["free8"]:
        service_port = 5008
        service_url = f"http://localhost:{service_port}/health"

        try:
            response = requests.get(service_url, timeout=5)
            api_config["last_test_time"] = datetime.now().isoformat()
            if response.status_code == 200:
                api_config["available"] = True
                api_config["last_test_result"] = "success"
                api_config["success_count"] += 1
                print(f"[启动测试] {api_name} 独立服务可用")
                return True
            else:
                api_config["available"] = False
                api_config["last_test_result"] = f"failed: {response.status_code}"
                api_config["failure_count"] += 1
                print(f"[启动测试] {api_name} 独立服务不可用: {response.status_code}")
                return False
        except Exception as e:
            api_config["available"] = False
            api_config["last_test_time"] = datetime.now().isoformat()
            api_config["last_test_result"] = f"error: {str(e)}"
            api_config["failure_count"] += 1
            print(f"[启动测试] {api_name} 独立服务测试失败: {e}")
            return False

    try:
        endpoint = api_config.get("endpoint", "/v1/chat/completions")
        url = f"{base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        proxies = None
        if use_proxy and config.HTTP_PROXY:
            proxies = {
                "http": config.HTTP_PROXY,
                "https": config.HTTP_PROXY
            }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }

        response = requests.post(url, headers=headers, json=payload, proxies=proxies, timeout=30)
        api_config["last_test_time"] = datetime.now().isoformat()

        if response.status_code == 200:
            api_config["available"] = True
            api_config["last_test_result"] = "success"
            api_config["success_count"] += 1
            print(f"[启动测试] {api_name} 可用")
            return True
        else:
            api_config["available"] = False
            api_config["last_test_result"] = f"failed: {response.status_code}"
            api_config["failure_count"] += 1
            print(f"[启动测试] {api_name} 不可用: {response.status_code}")
            return False
    except requests.exceptions.Timeout as e:
        api_config["available"] = False
        api_config["last_test_time"] = datetime.now().isoformat()
        api_config["last_test_result"] = f"timeout: {str(e)}"
        api_config["failure_count"] += 1
        print(f"[启动测试] {api_name} 测试超时: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        api_config["available"] = False
        api_config["last_test_time"] = datetime.now().isoformat()
        api_config["last_test_result"] = f"connection_error: {str(e)}"
        api_config["failure_count"] += 1
        print(f"[启动测试] {api_name} 连接错误: {e}")
        return False
    except Exception as e:
        api_config["available"] = False
        api_config["last_test_time"] = datetime.now().isoformat()
        api_config["last_test_result"] = f"error: {str(e)}"
        api_config["failure_count"] += 1
        print(f"[启动测试] {api_name} 测试失败: {e}")
        return False

def test_all_apis_startup():
    """启动时测试所有API"""
    print("\n[启动测试] 开始测试所有API...")

    app_state.clear_available_apis()
    
    total_apis = len(app_state.get_all_apis())
    successful_apis = []
    failed_apis = []

    for api_name in app_state.get_all_apis():
        api_config = app_state.get_api(api_name)
        if api_config and api_config.get("api_key"):
            if test_api_startup(api_name):
                app_state.add_available_api(api_name)
                successful_apis.append(api_name)
            else:
                failed_apis.append(api_name)
        else:
            print(f"[跳过] {api_name}: 未配置API_KEY")

    available = app_state.get_available_apis()
    
    # 优化：即使部分API测试失败，也允许启动服务
    print(f"\n[启动测试] 测试完成")
    print(f"[启动测试] 总计API: {total_apis}, 可用: {len(available)}, 失败: {len(failed_apis)}")
    
    if successful_apis:
        print(f"[启动测试] ✅ 可用API列表: {successful_apis}")
    if failed_apis:
        print(f"[启动测试] ⚠️  测试失败API列表: {failed_apis}")
        print(f"[启动测试] 提示: 可用API数量较少，部分请求可能失败")
    
    # 即使没有可用API也允许启动（会在运行时动态测试）
    if not available:
        print(f"[警告] 没有可用的API！服务将启动但无法处理请求")

def get_next_available_api():
    """获取下一个可用的API（基于权重选择）"""
    # 清理过期的黑名单记录
    app_state.cleanup_failed_apis()

    available_list = app_state.get_available_apis()

    if not available_list:
        return None

    # 过滤掉黑名单中的 API
    filtered_list = [api_name for api_name in available_list if not app_state.is_api_blacklisted(api_name)]

    if not filtered_list:
        # 如果所有 API 都在黑名单中，使用原始列表
        print(f"[警告] 所有可用的 API 都在黑名单中，使用原始列表")
        filtered_list = available_list
    else:
        print(f"[选择] 可用 API 数量: {len(filtered_list)}/{len(available_list)}")

    # 检查是否有特别权重的API
    special_weight_apis = []
    for api_name in filtered_list:
        weight = app_state.get_weight(api_name, 10)
        if weight > config.SPECIAL_WEIGHT_THRESHOLD:
            special_weight_apis.append((api_name, weight))

    if special_weight_apis:
        special_weight_apis.sort(key=lambda x: x[1], reverse=True)
        selected_api = special_weight_apis[0][0]
        print(f"[权重] 特别权重选中: {selected_api} (权重: {special_weight_apis[0][1]})")
        return selected_api

    # 按权重随机选择
    weights = [app_state.get_weight(api_name, 10) for api_name in filtered_list]
    total_weight = sum(weights)

    if total_weight <= 0:
        selected_api = filtered_list[0]
    else:
        r = random.randint(1, total_weight)
        cumulative = 0
        selected_api = filtered_list[0]
        for i, api_name in enumerate(filtered_list):
            cumulative += weights[i]
            if r <= cumulative:
                selected_api = api_name
                break

    return selected_api

def mark_api_failure(api_name):
    """标记API失败"""
    api_config = app_state.get_api(api_name)
    if not api_config:
        return
    
    api_config["consecutive_failures"] = api_config.get("consecutive_failures", 0) + 1
    api_config["failure_count"] += 1
    
    consecutive = api_config["consecutive_failures"]
    print(f"[API状态] {api_name} 连续失败次数: {consecutive}/{config.MAX_CONSECUTIVE_FAILURES}")
    
    if consecutive >= config.MAX_CONSECUTIVE_FAILURES:
        app_state.remove_available_api(api_name)
        api_config["available"] = False
        api_config["last_test_result"] = f"marked invalid after {consecutive} consecutive failures"
        print(f"[API状态] {api_name} 已标记为无效")

def mark_api_success(api_name):
    """标记API成功"""
    api_config = app_state.get_api(api_name)
    if not api_config:
        return
    
    api_config["consecutive_failures"] = 0
    api_config["success_count"] += 1
    
    if api_name not in app_state.get_available_apis() and api_config.get("api_key"):
        app_state.add_available_api(api_name)
        api_config["available"] = True
        print(f"[API状态] {api_name} 已恢复并重新加入可用列表")

def decrease_api_weight(api_name, reduction=1):
    """自动减少API权重"""
    current_weight = app_state.get_weight(api_name, 10)

    if current_weight > config.SPECIAL_WEIGHT_THRESHOLD:
        if current_weight > config.MIN_AUTO_DECREASE_WEIGHT:
            new_weight = max(config.MIN_AUTO_DECREASE_WEIGHT, current_weight - reduction)
            app_state.set_weight(api_name, new_weight)
            print(f"[权重] {api_name} 权重自动减少: {current_weight} -> {new_weight} (减少: {reduction})")

# ==================== 路由定义 ====================

@app.route('/debug', methods=['GET'])
def debug_page():
    """调试页面"""
    if not config.DEBUG_MODE:
        return "Debug mode not enabled", 403
    return render_template('debug.html')

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """兼容 OpenAI API 格式的聊天完成端点"""
    # 检查重启标志
    if app_state.restart_flag:
        print("\n[重启] 检测到配置变化，重新加载...")
        try:
            load_env()
            app_state.restart_flag = False
            print("[重启] 重新加载完成")
        except Exception as e:
            print(f"[错误] 重新加载失败: {e}")
            return jsonify({"error": f"Configuration reload failed: {str(e)}"}), 500

    # 并发控制
    max_wait_time = 120
    wait_start = time.time()

    while True:
        if app_state.get_active_requests() < config.MAX_CONCURRENT_REQUESTS:
            app_state.increment_active_requests()
            break

        elapsed = time.time() - wait_start
        if elapsed > max_wait_time:
            print(f"[并发] 等待超时 (已等待 {elapsed:.1f}s)")
            app_state.set_error(ErrorType.CONCURRENT_LIMIT.value, 
                              f"Concurrent limit exceeded: {app_state.get_active_requests()}/{config.MAX_CONCURRENT_REQUESTS}")
            return jsonify({
                "error": "Server too busy - concurrent request limit exceeded",
                "current": app_state.get_active_requests(),
                "limit": config.MAX_CONCURRENT_REQUESTS
            }), 503

        time.sleep(0.1)

    try:
        data = request.get_json()
        message_id = str(time.time())

        print(f"[请求] 收到请求 (ID: {message_id})")

        try:
            result, retry_count, used_api_name = execute_with_free_api(data, message_id)
        except NoAvailableAPIError as e:
            print(f"[错误] 没有可用的上游API: {str(e)}")
            available_apis = app_state.get_available_apis()
            all_apis = list(app_state.get_all_apis().keys())
            return jsonify({
                "error": {
                    "message": "All upstream APIs are unavailable. Please try again later.",
                    "type": "upstream_unavailable",
                    "available_count": len(available_apis),
                    "total_count": len(all_apis)
                }
            }), 503

        print(f"[请求] 请求成功 (ID: {message_id}, API: {used_api_name}, 重试: {retry_count})")
        
        update_call_stats(success=True)
        
        if retry_count > 0:
            update_call_stats(success=True, is_timeout=False)

        return jsonify(result), 200

    except TimeoutError as e:
        print(f"[请求] 超时: {str(e)}")
        app_state.set_error(ErrorType.TIMEOUT.value, str(e))
        update_call_stats(success=False, is_timeout=True)
        return jsonify({
            "error": {
                "message": "Request timeout, please try again",
                "type": "timeout"
            }
        }), 504

    except FormatError as e:
        print(f"[请求] 格式错误（所有上游API均失败）: {str(e)}")
        app_state.set_error(ErrorType.API_ERROR.value, str(e))
        update_call_stats(success=False)
        available_apis = app_state.get_available_apis()
        all_apis = list(app_state.get_all_apis().keys())
        return jsonify({
            "error": {
                "message": "All upstream APIs returned invalid responses. Please try again later.",
                "type": "invalid_response",
                "details": str(e),
                "available_count": len(available_apis),
                "total_count": len(all_apis)
            }
        }), 502

    except Exception as e:
        print(f"[错误] 请求失败: {str(e)}")
        app_state.set_error(ErrorType.UNKNOWN.value, str(e))
        update_call_stats(success=False)
        return jsonify({"error": str(e)}), 500

    finally:
        app_state.decrement_active_requests()
        print(f"[并发] 请求完成 (当前: {app_state.get_active_requests()}/{config.MAX_CONCURRENT_REQUESTS})")

@app.route('/v1/models', methods=['GET'])
def list_models():
    """列出所有API支持的模型"""
    models = []
    for api_name, api_config in app_state.get_all_apis().items():
        models.append({
            "id": api_config["model"],
            "object": "model",
            "owned_by": api_name,
            "permission": []
        })

    return jsonify({
        "object": "list",
        "data": models
    })

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

@app.route('/health/upstream', methods=['GET'])
def health_upstream():
    """检查上游 API 连接状态"""
    available = app_state.get_available_apis()
    return jsonify({
        "status": "ok" if available else "degraded",
        "available_apis": available,
        "total_apis": len(app_state.get_all_apis())
    })

@app.route('/debug/stats', methods=['GET'])
def debug_stats():
    """获取调试统计信息"""
    try:
        cache_dir = config.CACHE_DIR or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        if not cache_dir:
            return jsonify({
                "total": 0,
                "success": 0,
                "failed": 0,
                "timeout": 0,
                "retry": 0,
                "date": datetime.now().strftime("%Y%m%d"),
                "last_updated": datetime.now().isoformat()
            })

        today = datetime.now().strftime("%Y%m%d")
        counter_file = Path(cache_dir) / f"CALLS_{today}.json"

        if counter_file.exists():
            with open(counter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        else:
            return jsonify({
                "total": 0,
                "success": 0,
                "failed": 0,
                "timeout": 0,
                "retry": 0,
                "date": today,
                "last_updated": datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug/apis', methods=['GET'])
def debug_apis():
    """获取所有API的状态"""
    return jsonify({
        "free_apis": app_state.get_all_apis(),
        "available_apis": app_state.get_available_apis()
    })

@app.route('/debug/concurrency', methods=['GET'])
def debug_concurrency():
    """获取并发状态"""
    return jsonify({
        "active_requests": app_state.get_active_requests(),
        "max_concurrent": config.MAX_CONCURRENT_REQUESTS,
        "last_error": app_state.get_error(),
        "call_history": app_state.get_history()
    })

@app.route('/debug/api/enable', methods=['POST'])
def enable_api():
    """启用指定的API"""
    try:
        data = request.get_json()
        api_name = data.get('api_name')

        if not api_name or api_name not in app_state.get_all_apis():
            return jsonify({"success": False, "error": "Invalid API name"}), 400

        api_config = app_state.get_api(api_name)
        if api_config and api_config.get("api_key"):
            app_state.add_available_api(api_name)
            api_config["available"] = True
            return jsonify({"success": True, "message": f"{api_name} enabled"})
        else:
            return jsonify({"success": False, "error": "API key not configured"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug/api/disable', methods=['POST'])
def disable_api():
    """停用指定的API"""
    try:
        data = request.get_json()
        api_name = data.get('api_name')

        if not api_name or api_name not in app_state.get_all_apis():
            return jsonify({"success": False, "error": "Invalid API name"}), 400

        app_state.remove_available_api(api_name)
        api_config = app_state.get_api(api_name)
        if api_config:
            api_config["available"] = False

        return jsonify({"success": True, "message": f"{api_name} disabled"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug/api/weight', methods=['POST'])
def set_api_weight():
    """设置API的权重"""
    try:
        data = request.get_json()
        api_name = data.get('api_name')
        weight = data.get('weight')

        if not api_name or api_name not in app_state.get_all_apis():
            return jsonify({"success": False, "error": "Invalid API name"}), 400

        if not isinstance(weight, int) or weight < 0:
            return jsonify({"success": False, "error": "Weight must be non-negative integer"}), 400

        app_state.set_weight(api_name, weight)
        return jsonify({"success": True, "message": f"Weight set to {weight}"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def load_free_api_config(api_name):
    """加载 Free API 的配置"""
    config_path = Path(__file__).parent.parent / "free_api_test" / api_name / "config.py"
    if not config_path.exists():
        return None
    
    try:
        spec = importlib.util.spec_from_file_location(f"{api_name}_config", config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        title_name = getattr(module, 'TITLE_NAME', None)
        base_url = getattr(module, 'BASE_URL', '')
        
        return {
            "title_name": title_name,
            "base_url": base_url
        }
    except Exception as e:
        print(f"[配置加载] {api_name} 配置加载失败: {e}")
        return None


@app.route('/debug/api/weight', methods=['GET'])
def get_api_weights():
    """获取所有API的权重配置"""
    try:
        api_details = {}
        all_last_models = app_state.get_all_last_used_models()
        
        for api_name in app_state.get_all_apis():
            api_config = app_state.get_api(api_name)
            
            api_info = load_free_api_config(api_name)
            
            title_display = ""
            if api_info:
                if api_info.get("title_name"):
                    title_display = api_info["title_name"]
                elif api_info.get("base_url"):
                    title_display = api_info["base_url"].replace("/", "/\n")
            
            api_details[api_name] = {
                "weight": app_state.get_weight(api_name, 10),
                "enabled": api_name in app_state.get_available_apis(),
                "model": all_last_models.get(api_name, api_config.get("model", "unknown") if api_config else "unknown"),
                "title_display": title_display
            }

        return jsonify({
            "api_weights": app_state.get_all_weights(),
            "api_details": api_details
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug/api/weight/reset', methods=['POST'])
def reset_api_weights():
    """重置所有API权重为默认值"""
    try:
        init_default_weights()
        return jsonify({"success": True, "message": "Weights reset to default"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug/api/test', methods=['POST'])
def test_single_api():
    """测试单个 API 的连通性"""
    try:
        data = request.get_json()
        api_name = data.get('api_name')

        if not api_name or api_name not in app_state.get_all_apis():
            return jsonify({"success": False, "error": "Invalid API name"}), 400

        # 验证API配置
        api_config = app_state.get_api(api_name)
        is_valid, error_msg = validate_api_config(api_name, api_config)
        
        if not is_valid:
            return jsonify({
                "success": False,
                "api_name": api_name,
                "error": "配置验证失败",
                "validation_error": error_msg,
                "message": f"请检查API配置: {error_msg}"
            }), 400

        result = test_api_startup(api_name)

        if result:
            app_state.add_available_api(api_name)
            message = f"{api_name} 测试成功，已加入可用列表"
        else:
            message = f"{api_name} 测试失败，请检查网络连接或API配置"

        return jsonify({
            "success": result,
            "api_name": api_name,
            "last_test_time": api_config.get("last_test_time"),
            "last_test_result": api_config.get("last_test_result"),
            "available": api_config.get("available", False),
            "message": message
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "message": "测试过程中发生错误"
        }), 500

@app.route('/debug/api/test/all', methods=['POST'])
def test_all_apis():
    """测试所有 API 的连通性"""
    try:
        results = {}
        for api_name in app_state.get_all_apis():
            result = test_api_startup(api_name)
            api_config = app_state.get_api(api_name)
            if result:
                app_state.add_available_api(api_name)
            results[api_name] = {
                "success": result,
                "last_test_time": api_config.get("last_test_time"),
                "last_test_result": api_config.get("last_test_result"),
                "available": api_config.get("available", False)
            }
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/debug/api/reload', methods=['POST'])
def reload_api_configs():
    """重新加载所有API配置"""
    try:
        print("[配置重载] 开始重新加载API配置...")
        
        # 清空现有配置
        app_state.clear_available_apis()
        
        # 重新加载环境变量
        load_env()
        
        # 重新加载配置
        load_api_configs()
        
        # 重新测试所有API
        test_all_apis_startup()
        
        available = app_state.get_available_apis()
        print(f"[配置重载] 重载完成，可用API: {len(available)}/{len(app_state.get_all_apis())}")
        
        return jsonify({
            "success": True,
            "message": "API配置已重新加载",
            "available_count": len(available),
            "total_count": len(app_state.get_all_apis()),
            "available_apis": available
        })
    except Exception as e:
        print(f"[配置重载] 重载失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def validate_response(result, api_name):
    """
    验证上游响应是否有效
    返回: (is_valid, error_message)
    """
    if not isinstance(result, dict):
        return False, f"Response is not a dictionary: {type(result)}"
    
    if "error" in result:
        error_info = result["error"]
        if isinstance(error_info, dict):
            error_msg = error_info.get("message", str(error_info))
        else:
            error_msg = str(error_info)
        return False, f"上游返回错误: {error_msg}"
    
    if "choices" not in result:
        return False, "响应缺少 choices 字段"
    
    choices = result.get("choices", [])
    if not choices or len(choices) == 0:
        return False, "响应 choices 为空"
    
    first_choice = choices[0]
    if "message" not in first_choice:
        return False, "响应缺少 message 字段"
    
    message = first_choice.get("message", {})
    if "content" not in message and "reasoning_content" not in message:
        return False, "响应 message 缺少 content 和 reasoning_content"
    
    return True, None


def execute_with_free_api(data, message_id):
    """使用Free API执行请求"""
    retry_count = 0
    last_error = None
    used_api_name = None

    for attempt in range(config.MAX_RETRIES):
        api_name = get_next_available_api()

        if not api_name:
            raise NoAvailableAPIError("No available Free API")

        api_config = app_state.get_api(api_name)

        # 路由到独立服务（free8）
        if api_name in ["free8"]:
            service_port = 5008
            service_url = f"http://localhost:{service_port}/v1/chat/completions"

            try:
                print(f"[请求] 路由到 {api_name} 独立服务: {service_url}")

                # 检查独立服务是否可用
                models_url = f"http://localhost:{service_port}/v1/models"
                models_response = session.get(models_url, timeout=5)
                if models_response.status_code != 200:
                    raise Exception(f"{api_name} 独立服务不可用")

                # 发送聊天请求到独立服务
                current_timeout = config.TIMEOUT_RETRY if attempt > 0 else config.TIMEOUT_BASE
                response = session.post(
                    service_url,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=current_timeout
                )
                response.raise_for_status()

                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type.lower():
                    print(f"[错误] {api_name} 返回HTML而非JSON")
                    raise Exception(f"Upstream {api_name} returned HTML instead of JSON")

                # 诊断：记录原始响应
                response_text = response.text
                print(f"[诊断] {api_name} 上游响应状态码: {response.status_code}")
                print(f"[诊断] {api_name} 上游响应Content-Type: {content_type}")
                print(f"[诊断] {api_name} 上游响应长度: {len(response_text)} 字符")

                if not response_text or response_text.strip() == '':
                    print(f"[错误] {api_name} 上游返回空响应")
                    raise Exception(f"Empty response from {api_name}")

                if len(response_text) < 50:
                    print(f"[诊断] {api_name} 上游响应内容: {response_text[:200]}")

                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    print(f"[错误] {api_name} JSON解析失败: {str(e)}")
                    print(f"[错误] {api_name} 原始响应 (前500字符): {response_text[:500]}")
                    app_state.mark_api_failed_temporarily(api_name)
                    decrease_api_weight(api_name, reduction=50)
                    raise FormatError(f"Invalid JSON response from {api_name}: {str(e)}")

                is_valid, error_msg = validate_response(result, api_name)
                if not is_valid:
                    print(f"[错误] {api_name} 响应验证失败: {error_msg}")
                    print(f"[错误] {api_name} 原始响应 (前500字符): {response_text[:500]}")
                    app_state.mark_api_failed_temporarily(api_name)
                    decrease_api_weight(api_name, reduction=50)
                    raise FormatError(f"Invalid response from {api_name}: {error_msg}")

                print(f"[请求] {api_name} 独立服务成功")

                used_model = data.get("model", "unknown") if isinstance(data, dict) else "unknown"
                app_state.set_last_used_model(api_name, used_model)

                mark_api_success(api_name)
                used_api_name = api_name

                return result, retry_count, used_api_name

            except Exception as e:
                last_error = e
                print(f"[请求] {api_name} 独立服务失败: {str(e)}")

                # 标记失败
                mark_api_failure(api_name)

                if attempt < config.MAX_RETRIES - 1:
                    retry_count += 1
                    wait_time = 2 ** attempt
                    print(f"[重试] {wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue

                raise last_error

        try:
            # 简化的请求执行逻辑
            endpoint = api_config.get("endpoint", "/v1/chat/completions")
            url = f"{api_config['base_url']}{endpoint}"
            headers = {
                'Authorization': f'Bearer {api_config["api_key"]}',
                'Content-Type': 'application/json'
            }

            proxies = None
            if api_config.get("use_proxy") and config.HTTP_PROXY:
                proxies = {
                    "http": config.HTTP_PROXY,
                    "https": config.HTTP_PROXY
                }

            current_timeout = config.TIMEOUT_RETRY if attempt > 0 else config.TIMEOUT_BASE
            print(f"[请求] 发送到 {api_name} (尝试 {attempt + 1}/{config.MAX_RETRIES})")

            request_data = {
                "model": api_config.get("model"),
                "messages": data.get("messages", []),
                "temperature": data.get("temperature", config.DEFAULT_TEMPERATURE),
                "max_tokens": data.get("max_tokens", api_config.get("max_tokens", config.DEFAULT_MAX_TOKENS)),
                "top_p": data.get("top_p", config.DEFAULT_TOP_P),
            }

            response = session.post(
                url,
                json=request_data,
                headers=headers,
                proxies=proxies,
                timeout=current_timeout
            )
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'text/html' in content_type.lower():
                print(f"[错误] {api_name} 返回HTML而非JSON")
                raise Exception(f"Upstream {api_name} returned HTML instead of JSON")

            # 诊断：记录原始响应
            response_text = response.text
            print(f"[诊断] {api_name} 上游响应状态码: {response.status_code}")
            print(f"[诊断] {api_name} 上游响应Content-Type: {content_type}")
            print(f"[诊断] {api_name} 上游响应长度: {len(response_text)} 字符")

            if not response_text or response_text.strip() == '':
                print(f"[错误] {api_name} 上游返回空响应")
                raise Exception(f"Empty response from {api_name}")

            if len(response_text) < 50:
                print(f"[诊断] {api_name} 上游响应内容: {response_text[:200]}")

            try:
                result = response.json()
            except json.JSONDecodeError as e:
                print(f"[错误] {api_name} JSON解析失败: {str(e)}")
                print(f"[错误] {api_name} 原始响应 (前500字符): {response_text[:500]}")
                app_state.mark_api_failed_temporarily(api_name)
                decrease_api_weight(api_name, reduction=50)
                raise FormatError(f"Invalid JSON response from {api_name}: {str(e)}")

            is_valid, error_msg = validate_response(result, api_name)
            if not is_valid:
                print(f"[错误] {api_name} 响应验证失败: {error_msg}")
                print(f"[错误] {api_name} 原始响应 (前500字符): {response_text[:500]}")
                app_state.mark_api_failed_temporarily(api_name)
                decrease_api_weight(api_name, reduction=50)
                raise FormatError(f"Invalid response from {api_name}: {error_msg}")

            used_model = api_config.get("model", "unknown")
            app_state.set_last_used_model(api_name, used_model)
            
            mark_api_success(api_name)
            decrease_api_weight(api_name)
            used_api_name = api_name

            return result, retry_count, used_api_name

        except requests.exceptions.Timeout as e:
            last_error = e
            print(f"[请求] 超时 (尝试 {attempt + 1}/{config.MAX_RETRIES})")
            mark_api_failure(api_name)

            if attempt < config.MAX_RETRIES - 1:
                retry_count += 1
                wait_time = 2 ** attempt
                print(f"[重试] {wait_time}秒后重试...")
                time.sleep(wait_time)

        except requests.exceptions.ConnectionError as e:
            last_error = e
            print(f"[请求] 连接错误 (尝试 {attempt + 1}/{config.MAX_RETRIES})")
            mark_api_failure(api_name)

            if attempt < config.MAX_RETRIES - 1:
                retry_count += 1
                wait_time = 2 ** attempt
                print(f"[重试] {wait_time}秒后重试...")
                time.sleep(wait_time)

        except requests.exceptions.HTTPError as e:
            last_error = e
            status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
            print(f"[请求] HTTP错误 {status_code} (尝试 {attempt + 1}/{config.MAX_RETRIES})")
            mark_api_failure(api_name)

            if 500 <= status_code < 600 and attempt < config.MAX_RETRIES - 1:
                retry_count += 1
                wait_time = 2 ** attempt
                print(f"[重试] {wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                break

        except FormatError as e:
            # 格式错误：快速切换到下一个 API，不等待
            last_error = e
            print(f"[请求] 格式错误 - 快速切换到下一个 API: {str(e)}")
            mark_api_failure(api_name)

            if attempt < config.MAX_RETRIES - 1:
                retry_count += 1
                print(f"[重试] 立即尝试下一个 API...")
                continue

            raise last_error

        except Exception as e:
            last_error = e
            print(f"[请求] 失败 (尝试 {attempt + 1}/{config.MAX_RETRIES}): {str(e)}")
            mark_api_failure(api_name)
            break

    raise last_error if last_error else NoAvailableAPIError("Request failed")

def start_file_watcher():
    """启动文件监控"""
    observer = Observer()
    observer.schedule(FileChangeHandler(), path='.', recursive=False)
    observer.start()
    return observer

def main():
    """主函数"""
    load_env()
    load_api_configs()
    test_all_apis_startup()

    observer = start_file_watcher()

    if is_port_in_use(config.PORT):
        print(f"[错误] 端口 {config.PORT} 已被占用")
        sys.exit(1)

    print(f"[启动] 多Free API代理服务启动在端口 {config.PORT}")
    print(f"[启动] 可用API: {len(app_state.get_available_apis())}/{len(app_state.get_all_apis())}")

    try:
        app.run(host=config.HOST, port=config.PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[停止] 服务正在停止...")
        observer.stop()
        observer.join()
        print("[停止] 服务已停止")

if __name__ == "__main__":
    main()
