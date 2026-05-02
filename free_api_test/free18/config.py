# API配置
import os

TITLE_NAME = "Gemini"
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
MODEL_NAME = "gemini-3-flash-preview"
USE_PROXY = True
USE_SDK = True

# 请求参数默认值
MAX_TOKENS = 8192

# 默认权重（越高被选中概率越大）
# Gemini 需要代理，权重稍低一些
DEFAULT_WEIGHT = 60

# 响应格式配置
RESPONSE_FORMAT = {
    # Gemini 格式
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
