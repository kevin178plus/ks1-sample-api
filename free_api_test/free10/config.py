"""
free10 - 联通云 API 配置（使用联通云贵阳基地二区 API）
"""

# API 基础 URL（使用联通云贵阳基地二区，不添加 /v1）
BASE_URL = "https://aigw-gzgy2.cucloud.cn:8443"

# API Key（联通云 Coding Plan 专属 API Key）
API_KEY = "sk-sp-sVYnCcYWowtdBDVw5nXnGz9sdOm2IXFS"

# 模型配置（必须带 provider 前缀）
MODEL = "unicom-cloud/MiniMax-M2.5"

# 请求参数
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 8000

# 是否使用代理
USE_PROXY = False

# 超时设置（秒）
TIMEOUT = 30
