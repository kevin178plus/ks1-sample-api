# API配置
import os

API_KEY = os.getenv("FREE6_API_KEY")
BASE_URL = "https://models.csdn.net"
MODEL_NAME = "Deepseek-V3"
USE_PROXY = False  # 不使用代理
USE_SDK = False  # 使用HTTP API

# 请求参数默认值
MAX_TOKENS = 2000  # 最大生成token数

