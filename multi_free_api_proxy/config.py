"""
应用配置管理
"""
import os
from pathlib import Path


def get_cache_dir(fallback_subdir='cache'):
    """
    获取缓存目录，优先级：
    1. 环境变量 CACHE_DIR（最高优先级）
    2. R:\\api_proxy_cache（如果 R:\\ 驱动器存在，ramdisk 优先）
    3. 脚本目录下的缓存目录（回退方案）
    """
    # 1. 环境变量优先
    cache_dir = os.getenv("CACHE_DIR")
    if cache_dir:
        return cache_dir
    
    # 2. 检查 R:\ 是否存在（ramdisk）
    if os.path.exists('R:\\'):
        return 'R:\\api_proxy_cache'
    
    # 3. 回退到脚本目录
    script_dir = Path(__file__).parent.parent
    return str(script_dir / fallback_subdir)


class Config:
    """基础配置"""

    @staticmethod
    def is_debug_mode():
        """动态检查调试模式文件是否存在（相对于config.py所在目录）"""
        config_dir = Path(__file__).parent
        debug_file = config_dir / "DEBUG_MODE.txt"
        return debug_file.exists()

    @property
    def DEBUG_MODE(self):
        """动态检查调试模式"""
        return self.is_debug_mode()
    
    # 缓存配置
    CACHE_DIR = os.getenv("CACHE_DIR")
    
    # 代理配置
    HTTP_PROXY = os.getenv("HTTP_PROXY")
    
    # 并发配置
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    
    # 重试配置
    MAX_RETRIES = 3
    TIMEOUT_BASE = 45
    TIMEOUT_RETRY = 60
    
    # API 失败处理
    MAX_CONSECUTIVE_FAILURES = 3
    
    # 权重配置
    SPECIAL_WEIGHT_THRESHOLD = 100  # 权重大于此值时，下次请求必然选中
    MIN_AUTO_DECREASE_WEIGHT = 50   # 自动减少权重的下限
    
    # 默认参数
    DEFAULT_MAX_TOKENS = 2000
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TOP_P = 1.0
    DEFAULT_TOP_LOG_PROBS = 0
    DEFAULT_TOP_K = 0
    DEFAULT_STOP = None
    DEFAULT_PRESENCE_PENALTY = 0.0
    DEFAULT_FREQUENCY_PENALTY = 0.0
    DEFAULT_SEED = None
    
    # 服务配置
    PORT = int(os.getenv("PORT", "5000"))
    HOST = "0.0.0.0"
    
    # 文件监控
    WATCHED_FILES = {'.env', 'multi_free_api_proxy_v3.py'}
    
    # 调用历史
    CALL_HISTORY_MAXLEN = 10

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

def get_config():
    """获取配置对象"""
    env = os.getenv("FLASK_ENV", "production")
    if env == "development":
        return DevelopmentConfig()
    return ProductionConfig()
