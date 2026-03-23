"""
应用状态管理
集中管理所有全局状态，避免散落的全局变量
"""
import threading
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional

class AppState:
    """应用全局状态管理"""
    
    def __init__(self, config):
        self.config = config
        
        # 并发控制
        self.active_requests = 0
        self.request_queue = deque()
        self._active_lock = threading.Lock()
        self._queue_lock = threading.Lock()
        
        # API 管理
        self.free_apis = {}
        self.available_apis = deque()
        self._api_lock = threading.Lock()
        
        # 权重管理
        self.api_weights = {}
        self._weights_lock = threading.Lock()
        
        # 错误追踪
        self.last_error = {
            "type": "none",
            "message": "",
            "timestamp": None
        }
        self._error_lock = threading.Lock()
        
        # 调用历史
        self.call_history = deque(maxlen=config.CALL_HISTORY_MAXLEN)
        self._history_lock = threading.Lock()
        
        # 重启标志
        self.restart_flag = False
        
        # 最近使用的模型
        self.last_used_model = {}
        self._model_lock = threading.Lock()

        # 失败 API 临时黑名单（API名称 -> 失败时间）
        self.failed_apis = {}
        self._failed_apis_lock = threading.Lock()
        self.failed_api_blacklist_duration = 60  # 黑名单持续时间（秒）

    # ==================== 并发控制 ====================
    
    def increment_active_requests(self):
        """增加活跃请求数"""
        with self._active_lock:
            self.active_requests += 1
            return self.active_requests
    
    def decrement_active_requests(self):
        """减少活跃请求数"""
        with self._active_lock:
            self.active_requests = max(0, self.active_requests - 1)
            return self.active_requests
    
    def get_active_requests(self):
        """获取活跃请求数"""
        with self._active_lock:
            return self.active_requests
    
    # ==================== API 管理 ====================
    
    def add_api(self, api_name: str, api_config: Dict):
        """添加 API 配置"""
        with self._api_lock:
            self.free_apis[api_name] = api_config
    
    def get_api(self, api_name: str) -> Optional[Dict]:
        """获取 API 配置"""
        with self._api_lock:
            return self.free_apis.get(api_name)
    
    def get_all_apis(self) -> Dict:
        """获取所有 API 配置"""
        with self._api_lock:
            return dict(self.free_apis)
    
    def add_available_api(self, api_name: str):
        """添加可用 API"""
        with self._api_lock:
            if api_name not in self.available_apis:
                self.available_apis.append(api_name)
    
    def remove_available_api(self, api_name: str):
        """移除可用 API"""
        with self._api_lock:
            if api_name in self.available_apis:
                self.available_apis.remove(api_name)
    
    def get_available_apis(self) -> List[str]:
        """获取可用 API 列表"""
        with self._api_lock:
            return list(self.available_apis)
    
    def clear_available_apis(self):
        """清空可用 API 列表"""
        with self._api_lock:
            self.available_apis.clear()
    
    # ==================== 权重管理 ====================
    
    def set_weight(self, api_name: str, weight: int):
        """设置 API 权重"""
        with self._weights_lock:
            self.api_weights[api_name] = weight
    
    def get_weight(self, api_name: str, default: int = 10) -> int:
        """获取 API 权重"""
        with self._weights_lock:
            return self.api_weights.get(api_name, default)
    
    def get_all_weights(self) -> Dict[str, int]:
        """获取所有权重"""
        with self._weights_lock:
            return dict(self.api_weights)
    
    def init_weights(self, weights: Dict[str, int]):
        """初始化权重"""
        with self._weights_lock:
            self.api_weights.clear()
            self.api_weights.update(weights)
    
    # ==================== 错误追踪 ====================
    
    def set_error(self, error_type: str, message: str):
        """设置错误信息"""
        with self._error_lock:
            self.last_error = {
                "type": error_type,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_error(self) -> Dict:
        """获取错误信息"""
        with self._error_lock:
            return dict(self.last_error)
    
    def clear_error(self):
        """清空错误信息"""
        with self._error_lock:
            self.last_error = {
                "type": "none",
                "message": "",
                "timestamp": None
            }
    
    # ==================== 调用历史 ====================
    
    def add_history(self, record: Dict):
        """添加调用历史"""
        with self._history_lock:
            self.call_history.append(record)
    
    def get_history(self) -> List[Dict]:
        """获取调用历史"""
        with self._history_lock:
            return list(self.call_history)
    
    # ==================== 锁管理 ====================
    
    def get_lock(self, lock_name: str) -> Optional[threading.Lock]:
        """获取指定的锁"""
        locks = {
            'active': self._active_lock,
            'queue': self._queue_lock,
            'api': self._api_lock,
            'weights': self._weights_lock,
            'error': self._error_lock,
            'history': self._history_lock,
        }
        return locks.get(lock_name)
    
    # ==================== 最近使用模型 ====================
    
    def set_last_used_model(self, api_name: str, model: str):
        """设置最近使用的模型"""
        with self._model_lock:
            self.last_used_model[api_name] = model
    
    def get_last_used_model(self, api_name: str) -> Optional[str]:
        """获取最近使用的模型"""
        with self._model_lock:
            return self.last_used_model.get(api_name)
    
    def get_all_last_used_models(self) -> Dict[str, str]:
        """获取所有最近使用的模型"""
        with self._model_lock:
            return dict(self.last_used_model)

    # ==================== 失败 API 黑名单管理 ====================

    def mark_api_failed_temporarily(self, api_name: str):
        """将 API 标记为临时失败，加入黑名单"""
        with self._failed_apis_lock:
            self.failed_apis[api_name] = datetime.now().timestamp()
            print(f"[黑名单] {api_name} 已加入临时黑名单 ({self.failed_api_blacklist_duration}秒)")

    def is_api_blacklisted(self, api_name: str) -> bool:
        """检查 API 是否在黑名单中"""
        with self._failed_apis_lock:
            if api_name not in self.failed_apis:
                return False

            # 检查是否已过期
            failed_time = self.failed_apis[api_name]
            current_time = datetime.now().timestamp()

            if current_time - failed_time > self.failed_api_blacklist_duration:
                # 已过期，从黑名单移除
                del self.failed_apis[api_name]
                print(f"[黑名单] {api_name} 已从黑名单移除")
                return False

            return True

    def cleanup_failed_apis(self):
        """清理过期的失败 API 记录"""
        with self._failed_apis_lock:
            current_time = datetime.now().timestamp()
            expired_apis = []

            for api_name, failed_time in self.failed_apis.items():
                if current_time - failed_time > self.failed_api_blacklist_duration:
                    expired_apis.append(api_name)

            for api_name in expired_apis:
                del self.failed_apis[api_name]
                print(f"[黑名单] 清理过期的失败 API: {api_name}")
