# API配置
import os

TITLE_NAME = "Sambanova"
API_KEY = os.getenv("SAMBANOVA_API_KEY")
BASE_URL = "https://api.sambanova.ai/v1"
MODEL_NAME = "DeepSeek-V3.1"
USE_PROXY = False
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 4096

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 80

# 响应格式配置
RESPONSE_FORMAT = {
    # Sambanova 标准 OpenAI 格式
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
