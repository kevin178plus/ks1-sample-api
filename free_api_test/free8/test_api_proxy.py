#!/usr/bin/env python3
"""
Friendli.ai API 代理测试脚本
测试通过代理访问 zai-org/GLM-5 模型
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API 配置
api_key = os.getenv("FRIENDLI_TOKEN")
team_id = os.getenv("FRIENDLI_TEAM_ID")
if not api_key:
    raise ValueError("FRIENDLI_TOKEN not found in .env file")

# API 配置
BASE_URL = "https://api.friendli.ai/serverless/v1"
MODEL_NAME = "zai-org/GLM-5"

# 代理配置 - 强制使用代理
HTTP_PROXY = "http://127.0.0.1:7897"


def test_chat_completion_with_proxy(model=MODEL_NAME):
    """测试通过代理访问聊天完成 API"""
    print("=" * 50)
    print(f"测试 API: 聊天完成 (模型: {model}, 使用代理: True)")
    print("=" * 50)
    
    # 从 ask.txt 读取询问内容
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            ask_content = f.read()
        print("[OK] 成功读取 ask.txt")
    except Exception as e:
        print(f"[ERROR] 无法读取 ask.txt: {e}")
        return None, None
    
    # 配置代理
    proxies = {
        "http": HTTP_PROXY,
        "https": HTTP_PROXY
    }
    # 设置环境变量让 requests 使用代理
    os.environ["HTTP_PROXY"] = HTTP_PROXY
    os.environ["HTTPS_PROXY"] = HTTP_PROXY
    print(f"[INFO] 使用代理: {HTTP_PROXY}")
    
    import time
    start_time = time.time()
    
    try:
        # 使用 HTTP API 方式（通过代理）
        import requests
        session = requests.Session()
        session.proxies = proxies
        
        # 手动构建请求
        url = f"{BASE_URL}/chat/completions"
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        if team_id:
            headers['X-Friendli-Team'] = team_id
            
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": ask_content},
            ],
        }
        
        response = session.post(url, headers=headers, json=payload, timeout=120)
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
    print("Friendli.ai API 代理测试")
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"Team ID: {team_id if team_id else '未设置'}")
    print(f"Base URL: {BASE_URL}")
    print(f"模型: {MODEL_NAME}")
    print(f"代理: {HTTP_PROXY}\n")
    
    # 测试: 使用代理访问
    print("\n" + "=" * 60)
    print("测试: 通过代理访问 Friendli.ai API")
    print("=" * 60)
    result, time_info = test_chat_completion_with_proxy(MODEL_NAME)
    
    # 保存结果到 test_result_proxy.txt
    print("\n" + "=" * 60)
    print("保存测试结果")
    print("=" * 60)
    
    try:
        with open('test_result_proxy.txt', 'w', encoding='utf-8') as f:
            f.write("Friendli.ai API 代理测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"API Key: {api_key[:10]}...{api_key[-4:]}\n")
            f.write(f"Team ID: {team_id if team_id else '未设置'}\n")
            f.write(f"Base URL: {BASE_URL}\n")
            f.write(f"模型: {MODEL_NAME}\n")
            f.write(f"代理: {HTTP_PROXY}\n\n")
            
            # 从 ask.txt 读取询问内容
            with open('ask.txt', 'r', encoding='utf-8') as af:
                ask_content = af.read()
            
            f.write("询问内容 (来自 ask.txt):\n")
            f.write("-" * 60 + "\n")
            f.write(ask_content)
            f.write("\n" + "-" * 60 + "\n\n")
            
            # 写入测试结果
            f.write(f"\n{'=' * 60}\n")
            f.write(f"测试方式: 通过代理访问\n")
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
        
        print("[OK] 结果已保存到 test_result_proxy.txt")
    except Exception as e:
        print(f"[ERROR] 保存结果失败: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    if result is not None:
        status = "[OK] 成功"
        time_str = f"{time_info:.2f}秒"
        print(f"通过代理访问: {status} ({time_str})")
        return 0
    else:
        print(f"通过代理访问: [FAIL] 失败 ({time_info})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
