# API配置
import os

TITLE_NAME = "Mistral AI"
API_KEY = os.getenv("FREE4_API_KEY")
BASE_URL = "https://api.mistral.ai"
MODEL_NAME = "mistral-small-latest"
USE_PROXY = False  # 不使用代理
USE_SDK = False  # 使用HTTP API

# 请求参数默认值
MAX_TOKENS = 2000  # 最大生成token数

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 5
