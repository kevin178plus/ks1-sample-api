# 多Free API代理默认配置
# 此文件包含所有默认参数配置
# lastUpdated: 2026-02-23 19:29:43

# 请求参数默认值
DEFAULT_MAX_TOKENS = 2000  # 最大生成token数
DEFAULT_TEMPERATURE = 0.7  # 生成随机性 (0.0-2.0)
DEFAULT_TOP_P = 1.0  # 核采样概率 (0.0-1.0)
DEFAULT_TOP_LOG_PROBS = 0  # 顶级log概率数量
DEFAULT_STOP = None  # 停止序列 (str or list)
DEFAULT_PRESENCE_PENALTY = 0.0  # 存在惩罚 (-2.0 to 2.0)
DEFAULT_FREQUENCY_PENALTY = 0.0  # 频率惩罚 (-2.0 to 2.0)
DEFAULT_SEED = None  # 随机种子 (int or None)

# 超时配置
TIMEOUT_BASE = 45  # 基础超时时间（秒）
TIMEOUT_RETRY = 60  # 重试超时时间（秒）

# 重试配置
MAX_RETRIES = 3  # 最大重试次数

# 并发配置
MAX_CONCURRENT_REQUESTS = 5  # 最大并发请求数
