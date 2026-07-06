# API配置
import os

TITLE_NAME = "Agnes AI"
API_KEY = os.getenv("FREE25_API_KEY")
BASE_URL = "https://apihub.agnes-ai.com/v1"
MODEL_NAME = "agnes-2.0-flash"
USE_PROXY = False
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 4096

# 默认权重（越高被选中概率越大）
# Agnes AI 2.0-flash 512K 上下文，完全免费，国内直连
DEFAULT_WEIGHT = 10

# 响应格式配置
RESPONSE_FORMAT = {
    # 标准 OpenAI 格式
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}

# 可用模型列表
AVAILABLE_MODELS = [
    "agnes-2.0-flash",
]