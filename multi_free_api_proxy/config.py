"""
应用配置管理
"""
import os
from pathlib import Path

class Config:
    """基础配置"""
    # 调试模式
    DEBUG_MODE = Path('DEBUG_MODE.txt').exists()
    
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
