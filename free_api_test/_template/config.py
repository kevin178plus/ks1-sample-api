# API 配置
# 说明：此文件用于配置 Free API 的基本信息，可被 multi_free_api_proxy 自动加载
import os
from dotenv import load_dotenv

# ============ 基础配置 ============
# 服务名称（用于显示和日志）
TITLE_NAME = "API Provider Name"

# 加载 .env 文件中的环境变量
load_dotenv()

# API Key（从环境变量读取，需要在 .env 文件中配置）
# 环境变量命名规则：FREE{编号}_API_KEY，例如 FREE1_API_KEY
API_KEY = os.getenv("FREE{编号}_API_KEY")

# API 基础 URL
BASE_URL = "https://api.example.com"

# 默认模型名称
MODEL_NAME = "default-model-name"

# ============ 功能开关 ============
# 是否使用代理（True: 使用 HTTP_PROXY 环境变量配置的代理）
USE_PROXY = False

# 是否使用 SDK（True: 使用该提供商的官方 SDK，False: 使用标准 HTTP API）
# 注意：如果使用 SDK，需要在 config.py 中实现相应的 SDK 调用逻辑
USE_SDK = False

# ============ 请求参数默认值 ============
# 最大生成 token 数
MAX_TOKENS = 2000

# ============ 权重配置 ============
# 默认权重（越高被选中概率越大，multi_free_api_proxy 使用）
# 建议范围：10-200
# - 10-50: 低频使用
# - 50-100: 正常使用
# - 100-200: 高频使用/优先使用
DEFAULT_WEIGHT = 10

# ============ 响应格式配置 ============
# 定义如何从 API 响应中提取内容（multi_free_api_proxy 使用）
RESPONSE_FORMAT = {
    # 内容字段优先级列表（按优先级从高到低）
    # 常见字段：content, reasoning_content, thought 等
    "content_fields": ["content"],
    
    # 是否需要合并多个字段的内容
    "merge_fields": False,
    
    # 字段分隔符（如果需要合并）
    "field_separator": "\n\n---\n\n",
    
    # 是否在 content 为空时使用 reasoning_content 作为回退
    "use_reasoning_as_fallback": False
}

# ============ 可选配置 ============
# 可用模型列表（可选，如果为空则只使用 MODEL_NAME）
AVAILABLE_MODELS = []

# API 端点路径（可选，默认为 /v1/chat/completions）
ENDPOINT = "/v1/chat/completions"
