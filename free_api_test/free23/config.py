# API配置
import os

TITLE_NAME = "小米 MiMo"
API_KEY = os.getenv("FREE23_API_KEY")
BASE_URL = "https://api.xiaomimimo.com/v1"
MODEL_NAME = "mimo-v2.5-pro"
USE_PROXY = False
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 4096

# 默认权重（越高被选中概率越大）
# 小米 MiMo 国内直连，能力全面，权重较高
DEFAULT_WEIGHT = 100

# 响应格式配置
RESPONSE_FORMAT = {
    # 标准 OpenAI 格式
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}

# 可用模型列表
AVAILABLE_MODELS = [
    "mimo-v2.5-pro",
    "mimo-v2.5-tts",
    "mimo-v2-pro",
    "mimo-v2-flash",
]
