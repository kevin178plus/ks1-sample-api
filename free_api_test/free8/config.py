# API配置
# Friendli.ai API 配置
# 需要设置环境变量: FRIENDLI_TOKEN 和 FRIENDLI_TEAM_ID
import os

API_KEY = os.getenv("FRIENDLI_TOKEN")
TEAM_ID = os.getenv("FRIENDLI_TEAM_ID")
BASE_URL = "https://api.friendli.ai/serverless/v1"

# 可用模型列表（按优先级排序）
# 权重说明：如果没有特别指定权重，默认按列表顺序递减
# 例如 3 个模型时，权重为 3:2:1
AVAILABLE_MODELS = [
    # "meta-llama/Llama-3.3-70B-Instruct",
    "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "MiniMaxAI/MiniMax-M2.5",
    "zai-org/GLM-4.7",
    "zai-org/GLM-5",
]

# 默认模型（向后兼容）
MODEL_NAME = AVAILABLE_MODELS[0] if AVAILABLE_MODELS else "zai-org/GLM-5"

# 代理配置
USE_PROXY = False  # 是否使用代理
HTTP_PROXY = "http://127.0.0.1:7897"  # 代理地址

# SDK 配置
USE_SDK = True  # 使用 OpenAI SDK 格式

# 请求参数默认值
MAX_TOKENS = 2000  # 最大生成token数


def get_model_weights(models=None):
    """
    计算模型权重（按列表顺序递减）
    
    Args:
        models: 模型列表，如果为 None 则使用 AVAILABLE_MODELS
    
    Returns:
        list of tuples: [(model_name, weight), ...]
    
    示例:
        3 个模型 -> 权重为 3, 2, 1
        4 个模型 -> 权重为 4, 3, 2, 1
    """
    if models is None:
        models = AVAILABLE_MODELS
    
    n = len(models)
    if n == 0:
        return []
    
    # 权重从 n 递减到 1
    weights = list(range(n, 0, -1))
    return list(zip(models, weights))


def select_model_by_weight(models=None):
    """
    根据权重随机选择一个模型
    
    Args:
        models: 模型列表，如果为 None 则使用 AVAILABLE_MODELS
    
    Returns:
        str: 选中的模型名称
    """
    import random
    
    model_weights = get_model_weights(models)
    if not model_weights:
        raise ValueError("No models available")
    
    # 计算总权重
    total_weight = sum(w for _, w in model_weights)
    
    # 随机选择
    r = random.randint(1, total_weight)
    cumulative = 0
    
    for model, weight in model_weights:
        cumulative += weight
        if r <= cumulative:
            return model
    
    # 兜底返回权重最高的（第一个）
    return model_weights[0][0]


def get_weight_distribution(models=None):
    """
    获取模型权重分布（用于显示）
    
    Returns:
        dict: {model_name: {"weight": int, "percentage": float}}
    """
    model_weights = get_model_weights(models)
    if not model_weights:
        return {}
    
    total_weight = sum(w for _, w in model_weights)
    
    result = {}
    for model, weight in model_weights:
        result[model] = {
            "weight": weight,
            "percentage": round(weight / total_weight * 100, 1)
        }
    
    return result


if __name__ == "__main__":
    # 测试权重分配
    print("模型权重分配:")
    print("-" * 50)
    
    distribution = get_weight_distribution()
    for model, info in distribution.items():
        print(f"  {model}: 权重={info['weight']}, 占比={info['percentage']}%")
    
    print("\n模拟 60 次选择:")
    counts = {}
    for _ in range(60):
        model = select_model_by_weight()
        counts[model] = counts.get(model, 0) + 1
    
    for model, count in counts.items():
        print(f"  {model}: {count} 次")
