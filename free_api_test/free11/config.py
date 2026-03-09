"""
free11 - 白山智算 API 配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API Key
API_KEY = os.getenv("FREE11_API_KEY")

# API 基础 URL
BASE_URL = "https://api.edgefn.net"

# 模型配置
# 可用模型：
# - DeepSeek-R1-0528-Qwen3-8B
# - KAT-Coder-Exp-72B-1010
# - MiniMax-M2.5
MODEL_NAME = "DeepSeek-R1-0528-Qwen3-8B"

# 请求参数
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000

# 是否使用代理
USE_PROXY = False

# 超时设置（秒）
TIMEOUT = 30