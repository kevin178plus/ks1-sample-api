#!/usr/bin/env python3
"""
Mistral AI API 有效性测试脚本
测试 Mistral AI API 是否能正常工作
分别测试直接访问和通过代理访问
"""

import openai
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API 配置
api_key = os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("MISTRAL_API_KEY not found in .env file")

# 代理配置
HTTP_PROXY = "http://127.0.0.1:7897"

def test_chat_completion(model="mistral-small-latest", use_proxy=False):
    """测试聊天完成 API"""
    print("=" * 50)
    print(f"测试 API: 聊天完成 (模型: {model}, 代理: {use_proxy})")
    print("=" * 50)
    
    # 从 ask.txt 读取询问内容
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            ask_content = f.read()
        print("[OK] 成功读取 ask.txt")
    except Exception as e:
        print(f"[ERROR] 无法读取 ask.txt: {e}")
        return None, None
    
    # 配置 API
    openai.api_key = api_key
    openai.base_url = "https://api.mistral.ai/v1/"
    
    # 配置代理
    proxies = None
    if use_proxy:
        proxies = {
            "http": HTTP_PROXY,
            "https": HTTP_PROXY
        }
        # 设置环境变量让 requests 使用代理
        os.environ["HTTP_PROXY"] = HTTP_PROXY
        os.environ["HTTPS_PROXY"] = HTTP_PROXY
        print(f"[INFO] 使用代理: {HTTP_PROXY}")
    else:
        # 清除代理环境变量
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)
        print("[INFO] 直接访问（不使用代理）")
    
    try:
        import requests
        session = requests.Session()
        if use_proxy:
            session.proxies = proxies
        
        # 手动构建请求
        url = f"{openai.base_url}chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": ask_content,
                },
            ],
        }
        
        import time
        start_time = time.time()
        response = session.post(url, headers=headers, json=payload, timeout=60)
        elapsed_time = time.time() - start_time
        
        response.raise_for_status()
        result = response.json()
        
        # 获取回复内容
        result_content = result['choices'][0]['message']['content']
        
        print(f"[OK] API 调用成功！耗时: {elapsed_time:.2f}秒")
        
        return result_content, elapsed_time
        
    except Exception as e:
        print(f"[ERROR] API 调用错误: {e}")
        return None, str(e)

def main():
    """主函数"""
    print("Mistral AI API 有效性测试")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"Base URL: https://api.mistral.ai/v1/\n")
    
    # 存储测试结果
    results = []
    
    # 测试1: 直接访问
    print("\n" + "=" * 60)
    print("测试 1: 直接访问（不使用代理）")
    print("=" * 60)
    result1, time1 = test_chat_completion("mistral-small-latest", use_proxy=False)
    results.append(("直接访问", result1, time1))
    
    # 测试2: 通过代理访问
    print("\n" + "=" * 60)
    print("测试 2: 通过代理访问")
    print("=" * 60)
    result2, time2 = test_chat_completion("mistral-small-latest", use_proxy=True)
    results.append(("通过代理", result2, time2))
    
    # 保存结果到 test_result.txt
    print("\n" + "=" * 60)
    print("保存测试结果")
    print("=" * 60)
    
    try:
        with open('test_result.txt', 'w', encoding='utf-8') as f:
            f.write("Mistral AI API 测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"API Key: {api_key[:10]}...{api_key[-4:]}\n")
            f.write(f"Base URL: https://api.mistral.ai/v1/\n")
            f.write(f"模型: mistral-small-latest\n")
            f.write(f"代理: {HTTP_PROXY}\n\n")
            
            # 从 ask.txt 读取询问内容
            with open('ask.txt', 'r', encoding='utf-8') as af:
                ask_content = af.read()
            
            f.write("询问内容 (来自 ask.txt):\n")
            f.write("-" * 60 + "\n")
            f.write(ask_content)
            f.write("\n" + "-" * 60 + "\n\n")
            
            # 写入测试结果
            for test_name, result, time_info in results:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"测试方式: {test_name}\n")
                f.write("=" * 60 + "\n\n")
                
                if result is None:
                    f.write(f"状态: 失败\n")
                    f.write(f"错误信息: {time_info}\n")
                else:
                    f.write(f"状态: 成功\n")
                    f.write(f"耗时: {time_info:.2f}秒\n\n")
                    f.write("AI 回复:\n")
                    f.write("-" * 60 + "\n")
                    f.write(result)
                    f.write("\n" + "-" * 60 + "\n")
        
        print("[OK] 结果已保存到 test_result.txt")
    except Exception as e:
        print(f"[ERROR] 保存结果失败: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    success_count = sum(1 for _, r, _ in results if r is not None)
    total_count = len(results)
    
    for test_name, result, time_info in results:
        status = "✅ 成功" if result is not None else "❌ 失败"
        time_str = f"{time_info:.2f}秒" if result is not None else time_info
        print(f"{test_name}: {status} ({time_str})")
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
