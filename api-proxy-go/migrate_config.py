#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置迁移脚本
从 Python 版本迁移配置到 Go 版本
"""

import os
import sys
import re
import importlib.util
from pathlib import Path
from dotenv import load_dotenv


def load_env_file(env_path):
    """加载 .env 文件"""
    load_dotenv(env_path)
    return dict(os.environ)


def load_upstream_config(config_path):
    """加载上游配置（config.py）"""
    spec = importlib.util.spec_from_file_location("upstream_config", config_path)
    if spec is None or spec.loader is None:
        return None

    config_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(config_module)
    except Exception as e:
        print(f"[警告] 加载配置文件失败 {config_path}: {e}")
        return None

    return config_module


def generate_go_upstream_config(config_module, env_vars, api_key_env_var):
    """生成 Go 版本的上游配置"""
    # 获取配置值
    api_key = env_vars.get(api_key_env_var, getattr(config_module, "API_KEY", ""))
    base_url = getattr(config_module, "BASE_URL", "")
    model_name = getattr(config_module, "MODEL_NAME", "")
    use_proxy = getattr(config_module, "USE_PROXY", False)
    use_sdk = getattr(config_module, "USE_SDK", False)
    max_tokens = getattr(config_module, "MAX_TOKENS", 2000)
    default_weight = getattr(config_module, "DEFAULT_WEIGHT", 10)

    # 响应格式配置
    response_format = getattr(config_module, "RESPONSE_FORMAT", {
        "content_fields": ["content"],
        "merge_fields": False,
        "use_reasoning_as_fallback": False
    })

    # 生成 YAML 配置
    yaml_content = f"""name: "{config_module.__name__.replace('upstream_config_', '')}"
address: "{base_url}"
api_key: "{api_key}"
enabled: true
default_weight: {default_weight}

# 限额配置（根据实际情况调整）
limit:
  hourly: 1000
  daily: 5000
  monthly: 100000

# 阈值配置
thresholds:
  warning: 80
  critical: 95

# 代理配置
use_proxy: {str(use_proxy).lower()}
use_sdk: {str(use_sdk).lower()}

# 模型配置
model: "{model_name}"
available_models: []
use_weighted_model: false

# 响应格式配置
response_format:
  content_fields: {response_format.get('content_fields', ['content'])}
  merge_fields: {str(response_format.get('merge_fields', False)).lower()}
  use_reasoning_as_fallback: {str(response_format.get('use_reasoning_as_fallback', False)).lower()}

# 最大 token 数
max_tokens: {max_tokens}
"""

    return yaml_content


def generate_go_main_config(env_vars):
    """生成 Go 版本的主配置"""
    cache_dir = env_vars.get("CACHE_DIR", "./cache")
    http_proxy = env_vars.get("HTTP_PROXY", "")
    max_concurrent = env_vars.get("MAX_CONCURRENT_REQUESTS", "5")

    yaml_content = f"""# API 代理配置文件（从 Python 版本自动迁移）

# 监听地址
listen: ":8080"

# 上游配置
upstreams:
  root_dir: "./upstreams"  # 上游配置根目录

# 认证配置
auth:
  enabled: false          # 是否启用认证
  keys: []                # API Key 白名单，为空则允许所有
  key_limit: false        # 是否启用按密钥限额统计
  default_limit: 1000     # 默认限额（调用次数）

# 限流配置
rate_limit:
  enabled: true                   # 是否启用限流
  requests_per_second: {max_concurrent}  # 每秒请求数限制（从 MAX_CONCURRENT_REQUESTS 迁移）

# 调试配置
debug:
  enabled: true             # 是否启用调试模式
  cache_dir: "{cache_dir}"  # 缓存目录（从 CACHE_DIR 迁移）
  traffic_log:
    enabled: true           # 是否启用流量日志
    path: "{cache_dir}/traffic.json"
    max_size_mb: 100
    max_backups: 3
    compress: true
    buffer_size: 1000
    record_body: true
    max_body_bytes: 1024

# 健康检查配置
health_check:
  enabled: true             # 是否启用健康检查
  interval: 12h             # 检查间隔，默认 12 小时
  timeout: 30s              # 检查超时时间
  max_failures: 3           # 最大连续失败次数

# 权重配置
weight:
  special_threshold: 100    # 特别权重阈值，>100 次必然选中
  min_auto_decrease: 50     # 自动减少权重的下限
"""

    return yaml_content


def migrate_config():
    """执行配置迁移"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    go_project_root = script_dir
    python_project_root = script_dir.parent

    print(f"Python 项目根目录: {python_project_root}")
    print(f"Go 项目根目录: {go_project_root}")

    # 1. 加载 .env 文件
    env_path = python_project_root / ".env"
    if not env_path.exists():
        print(f"[错误] .env 文件不存在: {env_path}")
        return False

    print(f"\n[1/4] 加载 .env 文件...")
    env_vars = load_env_file(env_path)
    print(f"  ✓ 已加载 {len(env_vars)} 个环境变量")

    # 2. 生成主配置文件
    print(f"\n[2/4] 生成主配置文件...")
    main_config = generate_go_main_config(env_vars)
    main_config_path = go_project_root / "config.yaml"
    with open(main_config_path, "w", encoding="utf-8") as f:
        f.write(main_config)
    print(f"  ✓ 已生成: {main_config_path}")

    # 3. 扫描并迁移上游配置
    print(f"\n[3/4] 扫描上游配置...")
    free_api_dir = python_project_root / "free_api_test"
    upstreams_dir = go_project_root / "upstreams"

    # 创建上游目录
    upstreams_dir.mkdir(exist_ok=True)

    # 扫描所有 free* 子目录
    api_dirs = list(free_api_dir.glob("free*"))
    print(f"  找到 {len(api_dirs)} 个上游目录")

    migrated_count = 0
    for api_dir in sorted(api_dirs):
        api_name = api_dir.name
        config_file = api_dir / "config.py"

        if not config_file.exists():
            print(f"  - 跳过 {api_name}: 未找到 config.py")
            continue

        print(f"  - 迁移 {api_name}...")

        # 加载配置
        config_module = load_upstream_config(config_file)
        if config_module is None:
            print(f"    ✗ 加载失败")
            continue

        # 确定 API Key 环境变量名
        api_key_env_var = f"{api_name.upper()}_API_KEY"
        if api_name == "free7":
            api_key_env_var = "NVIDIA_API_KEY"

        # 生成 Go 配置
        upstream_config = generate_go_upstream_config(config_module, env_vars, api_key_env_var)

        # 创建上游目录
        upstream_dir = upstreams_dir / api_name
        upstream_dir.mkdir(exist_ok=True)

        # 写入配置文件
        upstream_config_path = upstream_dir / "config.yaml"
        with open(upstream_config_path, "w", encoding="utf-8") as f:
            f.write(upstream_config)

        print(f"    ✓ 已生成: {upstream_config_path}")
        migrated_count += 1

    print(f"\n  ✓ 已迁移 {migrated_count} 个上游配置")

    # 4. 完成
    print(f"\n[4/4] 配置迁移完成！")
    print(f"\n下一步:")
    print(f"  1. 检查配置文件: {main_config_path}")
    print(f"  2. 检查上游配置: {upstreams_dir}")
    print(f"  3. 根据需要调整限额配置（limit 部分）")
    print(f"  4. 编译并运行 Go 版本")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("配置迁移脚本 - Python → Go")
    print("=" * 60)

    try:
        success = migrate_config()
        if success:
            print("\n✓ 迁移成功！")
            sys.exit(0)
        else:
            print("\n✗ 迁移失败！")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ 迁移出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
