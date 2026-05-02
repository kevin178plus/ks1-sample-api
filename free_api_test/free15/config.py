# API配置
import os

TITLE_NAME = "Groq"
API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "llama-3.3-70b-versatile"
USE_PROXY = True
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 8192

# 默认权重（越高被选中概率越大）
# Groq 需要代理，权重稍低一些
DEFAULT_WEIGHT = 80

# 响应格式配置
RESPONSE_FORMAT = {
    # Groq 标准 OpenAI 格式
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
