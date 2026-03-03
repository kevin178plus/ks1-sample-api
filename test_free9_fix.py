"""测试 free9 修复后的配置"""
import sys
sys.path.insert(0, '.')

from multi_free_api_proxy.multi_free_api_proxy_v3 import load_api_configs, test_api_startup

# 加载配置
load_api_configs()

# 测试 free9
print("\n" + "="*50)
print("测试 free9 API")
print("="*50)
result = test_api_startup('free9')
print("="*50)
if result:
    print("✓ free9 测试成功")
else:
    print("✗ free9 测试失败")