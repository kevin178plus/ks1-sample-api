import requests
import json
import time

# 测试本地代理 (优化版)
BASE_URL = "http://localhost:5000"
TIMEOUT = 30  # 30秒超时

def test_endpoint(url, method="GET", data=None, description=""):
    """通用测试函数"""
    try:
        print(f"{description}")
        print(f"请求: {method} {url}")
        
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        else:  # POST
            response = requests.post(url, json=data, timeout=TIMEOUT)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 请求成功")
            result = response.json()
            if description.__contains__("健康检查"):
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            elif description.__contains__("模型"):
                print(f"模型数量: {len(result.get('data', []))}")
                print(f"可用模型: {[m['id'] for m in result.get('data', [])]}")
            elif description.__contains__("聊天"):
                print(f"模型: {result.get('model', '未知')}")
                print(f"回复: {result['choices'][0]['message']['content']}")
                print(f"使用量: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保服务已启动")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def main():
    print("=" * 60)
    print("本地 API 代理测试 (优化版)")
    print("=" * 60)
    print(f"测试地址: {BASE_URL}")
    print(f"超时设置: {TIMEOUT}秒")
    print()

    # 测试计数器
    passed_tests = 0
    total_tests = 4

    # 1. 健康检查
    if test_endpoint(f"{BASE_URL}/health", description="1️⃣ 健康检查"):
        passed_tests += 1
    print()

    # 2. 列出模型
    if test_endpoint(f"{BASE_URL}/v1/models", description="2️⃣ 列出可用模型"):
        passed_tests += 1
    print()

    # 3. 测试聊天完成 (中文)
    print("3️⃣ 测试聊天完成 (中文)")
    chinese_payload = {
        "messages": [
            {"role": "user", "content": "你好！请简单介绍一下你自己。"}
        ],
        "temperature": 0.7,
        "max_tokens": 200,
    }
    if test_endpoint(f"{BASE_URL}/v1/chat/completions", method="POST", data=chinese_payload):
        passed_tests += 1
    print()

    # 4. 测试聊天完成 (英文)
    print("4️⃣ 测试聊天完成 (英文)")
    english_payload = {
        "messages": [
            {"role": "user", "content": "Hello! Briefly introduce yourself."}
        ],
        "temperature": 0.7,
        "max_tokens": 200,
    }
    if test_endpoint(f"{BASE_URL}/v1/chat/completions", method="POST", data=english_payload):
        passed_tests += 1
    print()

    # 测试结果汇总
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"通过测试: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！API代理工作正常")
    elif passed_tests >= 2:
        print("⚠️  部分测试通过，基本功能正常")
    else:
        print("❌ 多数测试失败，请检查配置和服务状态")
    
    print("\n常见问题排查:")
    print("- 连接失败: 确保服务已启动 (python local_api_proxy.py)")
    print("- API错误: 检查.env文件中的OPENROUTER_API_KEY配置")
    print("- 请求超时: 检查网络连接和OpenRouter服务状态")

if __name__ == "__main__":
    main()