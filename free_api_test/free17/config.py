# API配置
import os

TITLE_NAME = "Cerebras"
API_KEY = os.getenv("CEREBRAS_API_KEY")
BASE_URL = "https://api.cerebras.ai/v1"
MODEL_NAME = "llama3.1-8b"
USE_PROXY = True
USE_SDK = True

# 请求参数默认值
MAX_TOKENS = 8192

# 默认权重（越高被选中概率越大）
# Cerebras 需要代理，权重稍低一些
DEFAULT_WEIGHT = 50

# 响应格式配置
RESPONSE_FORMAT = {
    # Cerebras 标准 OpenAI 格式
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
