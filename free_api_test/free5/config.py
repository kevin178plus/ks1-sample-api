# API配置
import os

# iflow SDK 不需要 API_KEY，但为了统一格式设置一个默认值
API_KEY = os.getenv("FREE5_API_KEY", "iflow-sdk")
BASE_URL = "iflow"
MODEL_NAME = "iflow"
USE_PROXY = False  # 不使用代理
USE_SDK = True  # 使用iflow SDK

# 请求参数默认值
MAX_TOKENS = 2000  # 最大生成token数

# 默认权重（越高被选中概率越大）
DEFAULT_WEIGHT = 15

# 响应格式配置
# iflow SDK 返回的是纯文本，不需要特殊处理
RESPONSE_FORMAT = {
    # SDK 直接返回文本内容，不需要从字段提取
    "content_fields": ["content"],
    "merge_fields": False,
    "use_reasoning_as_fallback": False
}
