# API配置
import os

API_KEY = os.getenv("FREE4_API_KEY")
BASE_URL = "https://api.mistral.ai"
MODEL_NAME = "mistral-small-latest"
USE_PROXY = False  # 不使用代理
USE_SDK = False  # 使用HTTP API
