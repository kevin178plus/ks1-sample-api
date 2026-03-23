"""
free12 - OpenCode AI API 配置
"""
import os
from dotenv import load_dotenv

TITLE_NAME = "OpenCode AI"

# 加载环境变量
load_dotenv()

# API Key
API_KEY = os.getenv("FREE12_API_KEY")

# 如果环境变量未设置，使用默认值（仅用于测试）
if not API_KEY:
    raise ValueError("FREE1_API_KEY not found in .env file")    
    
# API 基础 URL
BASE_URL = "https://opencode.ai/zen/v1"

# 模型配置
MODEL_NAME = "minimax-m2.5-free"

# 自定义端点（BASE_URL已包含/v1，这里只需要/chat/completions）
ENDPOINT = "/chat/completions"

# 请求参数
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000

# 是否使用代理
USE_PROXY = False

# 超时设置（秒）
TIMEOUT = 60
