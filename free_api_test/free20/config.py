# LongCat API 配置
import os

TITLE_NAME = "LongCat"
API_KEY = os.getenv("LONGCAT_API_KEY")
BASE_URL = "https://api.longcat.chat/openai/v1"
MODEL_NAME = "LongCat-Flash-Chat"
USE_PROXY = False
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 2000

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 100

# 支持的模型列表
AVAILABLE_MODELS = [
    "LongCat-Flash-Chat",        # 高性能通用对话模型
    "LongCat-Flash-Thinking",    # 深度思考模型（已升级至 2601）
    "LongCat-Flash-Thinking-2601", # 升级版深度思考模型
    "LongCat-Flash-Lite",        # 高效轻量化MoE模型
    "LongCat-Flash-Omni-2603",   # 多模态模型
    "LongCat-Flash-Chat-2602-Exp", # 高性能通用对话模型
    "LongCat-2.0-Preview",       # 高性能Agentic模型
]

# 响应格式配置
RESPONSE_FORMAT = {
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False,
}
