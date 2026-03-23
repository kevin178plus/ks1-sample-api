# API配置
import os

TITLE_NAME = "火山 Coding Plan"
API_KEY = os.getenv("FREE9_API_KEY")
BASE_URL = "https://ark.cn-beijing.volces.com/api/coding"
MODEL_NAME = "ark-code-latest"
USE_PROXY = False  # 不使用代理
USE_SDK = False  # 使用HTTP API
ENDPOINT = "/v3/chat/completions"  # 火山方舟使用 /v3 而非 /v1

# 请求参数默认值
MAX_TOKENS = 8192  # 最大生成token数

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 100

