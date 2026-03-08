#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试 free8 配置加载"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'multi_free_api_proxy'))

# 导入函数
from multi_free_api_proxy_v3 import load_env, load_api_configs

# 加载配置
load_env()
load_api_configs()

# 导入全局变量（在 load_api_configs 之后）
from multi_free_api_proxy_v3 import FREE_APIS

print('free8 配置:')
if 'free8' in FREE_APIS:
    config = FREE_APIS['free8']
    print(f"  use_weighted_model: {config.get('use_weighted_model')}")
    print(f"  available_models: {config.get('available_models')}")
    print(f"  model: {config.get('model')}")
    print(f"  response_format: {config.get('response_format')}")
else:
    print("  free8 未加载")