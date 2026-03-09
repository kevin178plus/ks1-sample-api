"""
错误处理模块
定义统一的错误类型和异常
"""
from enum import Enum

class ErrorType(Enum):
    """错误类型枚举"""
    NONE = "none"
    TIMEOUT = "timeout"
    UPSTREAM_UNREACHABLE = "upstream_unreachable"
    API_ERROR = "api_error"
    CONCURRENT_LIMIT = "concurrent_limit"
    PROXY_ERROR = "proxy_error"
    UNKNOWN = "unknown"

class APIError(Exception):
    """API 错误基类"""
    def __init__(self, error_type: ErrorType, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(message)

class TimeoutError(APIError):
    """超时错误"""
    def __init__(self, message: str = "Request timeout"):
        super().__init__(ErrorType.TIMEOUT, message)

class UpstreamError(APIError):
    """上游服务器错误"""
    def __init__(self, message: str = "Upstream server unreachable"):
        super().__init__(ErrorType.UPSTREAM_UNREACHABLE, message)

class ConcurrentLimitError(APIError):
    """并发限制错误"""
    def __init__(self, message: str = "Concurrent request limit exceeded"):
        super().__init__(ErrorType.CONCURRENT_LIMIT, message)

class ProxyError(APIError):
    """代理错误"""
    def __init__(self, message: str = "Proxy error"):
        super().__init__(ErrorType.PROXY_ERROR, message)

class NoAvailableAPIError(APIError):
    """没有可用 API 错误"""
    def __init__(self, message: str = "No available API"):
        super().__init__(ErrorType.API_ERROR, message)
