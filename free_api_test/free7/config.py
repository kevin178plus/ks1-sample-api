# API配置
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

API_KEY = os.getenv("FREE7_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/"
MODEL_NAME = "z-ai/glm4.7"
USE_PROXY = False  # 不使用代理
USE_SDK = False  # 使用HTTP API

# 请求参数默认值
MAX_TOKENS = 2000  # 最大生成token数

# 响应格式配置
# 定义如何从响应中提取内容
RESPONSE_FORMAT = {
    # 内容字段优先级列表（按优先级从高到低）
    "content_fields": ["content", "reasoning_content"],
    # 是否需要合并多个字段的内容
    "merge_fields": False,
    # 字段分隔符（如果需要合并）
    "field_separator": "\n\n---\n\n",
    # 是否在 content 为空时使用 reasoning_content
    "use_reasoning_as_fallback": True
}

