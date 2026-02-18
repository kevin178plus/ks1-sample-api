#!/usr/bin/env python3
"""
API 有效性测试脚本
测试 chatanywhere API 是否能正常工作
"""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API 配置
API_KEY = os.getenv("FREE2_API_KEY")
if not API_KEY:
    raise ValueError("FREE2_API_KEY not found in .env file")
BASE_URL = "https://api.chatanywhere.tech"

def test_models_endpoint():
    """测试模型列表 API"""
    print("=" * 50)
    print("测试 1: 列出可用模型")
    print("=" * 50)
    
    url = f"{BASE_URL}/v1/models"
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            print(f"[OK] 成功！找到 {len(models)} 个模型")
            print("\n部分可用模型:")
            for model in models[:5]:
                print(f"  - {model.get('id', 'unknown')}")
            return True
        else:
            print(f"[FAIL] 失败: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return False

def test_chat_completion(model="gpt-3.5-turbo"):
    """测试聊天完成 API"""
    print("\n" + "=" * 50)
    print(f"测试 2: 聊天完成 (模型: {model})")
    print("=" * 50)
    
    url = f"{BASE_URL}/v1/chat/completions"
    
    # 读取提示词
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            prompt = f.read()
    except Exception as e:
        print(f"[ERROR] 无法读取 ask.txt: {e}")
        return False
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的情感文案助手，擅长生成土味情话和浪漫情话。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.8,
        "max_tokens": 1500
    }
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            usage = data.get('usage', {})
            
            print(f"[OK] 成功！")
            print(f"\n使用的 Token:")
            print(f"  - 输入: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  - 输出: {usage.get('completion_tokens', 'N/A')}")
            print(f"  - 总计: {usage.get('total_tokens', 'N/A')}")
            
            # 写入文件避免编码问题
            with open('test_result.txt', 'w', encoding='utf-8') as f:
                f.write("API 测试结果\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"模型: {model}\n")
                f.write(f"输入 Token: {usage.get('prompt_tokens', 'N/A')}\n")
                f.write(f"输出 Token: {usage.get('completion_tokens', 'N/A')}\n")
                f.write(f"总计 Token: {usage.get('total_tokens', 'N/A')}\n\n")
                f.write("生成的回复:\n")
                f.write("-" * 50 + "\n")
                f.write(content)
                f.write("\n" + "-" * 50 + "\n")
            
            print(f"\n[OK] 结果已保存到 test_result.txt")
            return True
        else:
            print(f"[FAIL] 失败: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] 错误: {e}")
        return False

def main():
    """主函数"""
    print("ChatAnywhere API 有效性测试")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"Base URL: {BASE_URL}\n")
    
    results = []
    
    # 测试 1: 模型列表
    results.append(("模型列表", test_models_endpoint()))
    
    # 测试 2: 聊天完成 (使用轻量级模型)
    results.append(("聊天完成 (gpt-3.5-turbo)", test_chat_completion("gpt-3.5-turbo")))
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    for name, result in results:
        status = "[PASS] 通过" if result else "[FAIL] 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print(f"\n总体: {'[PASS] 所有测试通过' if all_passed else '[FAIL] 部分测试失败'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
