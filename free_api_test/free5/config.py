# API配置
import os

# iflow SDK 不需要 API_KEY，但为了统一格式设置一个默认值
API_KEY = os.getenv("FREE5_API_KEY", "iflow-sdk")
BASE_URL = "iflow"
MODEL_NAME = "iflow"
USE_PROXY = False  # 不使用代理
USE_SDK = True  # 使用iflow SDK
