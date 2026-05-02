# API配置
import os

TITLE_NAME = "Cohere"
API_KEY = os.getenv("COHERE_API_KEY")
BASE_URL = "https://api.cohere.com/v2"
MODEL_NAME = "command-a-03-2025"
USE_PROXY = True
USE_SDK = False

# 请求参数默认值
MAX_TOKENS = 4096

# 默认权重（越高被选中概率越大）
# Cohere 需要代理，权重稍低一些
DEFAULT_WEIGHT = 50

# 响应格式配置（需要特殊处理）
RESPONSE_FORMAT = {
    # Cohere 特有格式: message.content[0].text
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False,
    # 自定义字段映射函数
    "content_extractor": "lambda resp: resp.get('message', {}).get('content', [{}])[0].get('text', '') if resp.get('message', {}).get('content') else ''"
}