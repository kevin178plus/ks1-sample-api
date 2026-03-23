# API配置
import os

TITLE_NAME = "OpenRouter"
API_KEY = os.getenv("FREE1_API_KEY")
BASE_URL = "https://openrouter.ai"
MODEL_NAME = "openrouter/free"
USE_PROXY = True  # 使用代理
USE_SDK = False  # 使用HTTP API

# 请求参数默认值
MAX_TOKENS = 2000  # 最大生成token数

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 120

# 响应格式配置
RESPONSE_FORMAT = {
    # OpenRouter 标准格式，只使用 content 字段
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
