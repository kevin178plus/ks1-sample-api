# API配置
import os

TITLE_NAME = "FreeChatGPT"
API_KEY = os.getenv("FREE3_API_KEY")
BASE_URL = "https://free.v36.cm"
MODEL_NAME = "gpt-3.5-turbo"
USE_PROXY = False  # 不使用代理
USE_SDK = False  # 使用HTTP API

# 请求参数默认值
MAX_TOKENS = 2000  # 最大生成token数

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 10
