# FreeModel API 配置
import os

TITLE_NAME = "FreeModel"
API_KEY = os.getenv("FREEMODEL_API_KEY")
BASE_URL = "https://api.freemodel.dev"
MODEL_NAME = "freemodel-default"
USE_PROXY = False
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 2000

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 100

# 支持的模型列表
AVAILABLE_MODELS = [
    "freemodel-default",  # 默认模型
]

# 响应格式配置
RESPONSE_FORMAT = {
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False,
}
