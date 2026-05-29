# API配置
import os

TITLE_NAME = "ModelScope (魔搭)"
API_KEY = os.getenv("FREE24_API_KEY")
BASE_URL = "https://api-inference.modelscope.cn/v1"
MODEL_NAME = "Qwen/Qwen3.5-35B-A3B"
USE_PROXY = False
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 4096

# 默认权重（越高被选中概率越大）
# ModelScope 国内直连，2000次/天免费额度，模型丰富
DEFAULT_WEIGHT = 90

# 响应格式配置
RESPONSE_FORMAT = {
    # 标准 OpenAI 格式
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}

# 可用模型列表（ModelScope 模型ID = 模型在魔搭上的路径）
# 完整列表见 https://modelscope.cn/models?filter=inference_type
AVAILABLE_MODELS = [
    "Qwen/Qwen3.5-35B-A3B",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "ZhipuAI/GLM-4.7-Flash",
]
