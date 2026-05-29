# API配置
import os

TITLE_NAME = "SenseNova"
API_KEY = os.getenv("FREE22_API_KEY")
BASE_URL = "https://token.sensenova.cn/v1"
MODEL_NAME = "sensenova-6.7-flash-lite"
USE_PROXY = False
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 4096

# 默认权重（越高被选中概率越大）
# SenseNova 国内直连，免费额度充足，权重较高
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
    "sensenova-6.7-flash-lite",
    "sensenova-u1-fast",
    "deepseek-v4-flash",
]
