import requests
import json
import os
from pathlib import Path

# 测试本地代理
BASE_URL = "http://localhost:5000"

print("=" * 50)
print("测试本地 API 代理")
print("=" * 50)

# 0. 检查配置
print("\n0. 检查配置...")
try:
    # 检查.env文件
    env_file = Path('.env')
    if not env_file.exists():
        print("错误: .env文件不存在")
        exit(1)
    
    # 加载环境变量
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    
    print(f"API Key: {'已配置' if api_key else '未配置'}")
    print(f"API Key长度: {len(api_key) if api_key else 0}")
    print(f"测试模式: {'开启' if test_mode else '关闭'}")
    
    if not api_key and not test_mode:
        print("警告: 未配置API Key且未启用测试模式")
    
except Exception as e:
    print(f"配置检查错误: {e}")

# 1. 健康检查
print("\n1. 健康检查...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态: {response.json()}")
except Exception as e:
    print(f"错误: {e}")

# 2. 列出模型
print("\n2. 列出可用模型...")
try:
    response = requests.get(f"{BASE_URL}/v1/models")
    print(f"模型: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"错误: {e}")

# 3. 测试聊天完成
print("\n3. 测试聊天完成...")
try:
    payload = {
        "messages": [
            {"role": "user", "content": "Hello! What can you help me with today?"}
        ],
        "temperature": 0.7,
        "max_tokens": 500,
    }
    response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload)
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code != 200:
        print(f"错误响应: {response.text}")
        try:
            error_data = response.json()
            if "error" in error_data:
                print(f"详细错误: {error_data['error']}")
                # 检查是否是API认证问题
                if "401" in str(error_data['error']) or "Unauthorized" in str(error_data['error']):
                    print("提示: 这可能是API Key无效或过期导致的")
                    print("建议:")
                    print("  1. 检查OpenRouter账户余额")
                    print("  2. 重新生成API Key")
                    print("  3. 或启用测试模式: 在.env文件中添加 TEST_MODE=true")
        except:
            pass
    else:
        result = response.json()
        
        if "error" in result:
            print(f"API返回错误: {result['error']}")
        else:
            print(f"模型: {result.get('model')}")
            print(f"回复: {result['choices'][0]['message']['content']}")
            print(f"使用量: {result.get('usage')}")
            
            # 检查是否是测试模式响应
            if result.get('model') == 'openrouter/free' and '测试模式' in result['choices'][0]['message']['content']:
                print("注意: 当前运行在测试模式")
except Exception as e:
    print(f"请求异常: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
