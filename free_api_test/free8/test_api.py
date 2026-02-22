#!/usr/bin/env python3
"""
Friendli.ai API 测试脚本
测试多模型的聊天完成功能，支持分权制模型选择
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入配置
from config import (
    API_KEY, TEAM_ID, BASE_URL, AVAILABLE_MODELS,
    USE_PROXY, HTTP_PROXY, USE_SDK,
    select_model_by_weight, get_weight_distribution
)

if not API_KEY:
    raise ValueError("FRIENDLI_TOKEN not found in .env file")


def test_chat_completion(model=None, use_proxy=None, use_sdk=None):
    """测试聊天完成 API
    
    Args:
        model: 模型名称，如果为 None 则自动按权重选择
        use_proxy: 是否使用代理，如果为 None 则读取配置
        use_sdk: 是否使用 OpenAI SDK，如果为 None 则读取配置
    """
    # 使用配置默认值
    if use_proxy is None:
        use_proxy = USE_PROXY
    if use_sdk is None:
        use_sdk = USE_SDK
    if model is None:
        model = select_model_by_weight()
    
    print("=" * 50)
    print(f"测试 API: 聊天完成")
    print(f"  模型: {model}")
    print(f"  代理: {use_proxy}")
    print(f"  SDK: {use_sdk}")
    print("=" * 50)
    
    # 从 ask.txt 读取询问内容
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            ask_content = f.read()
        print("[OK] 成功读取 ask.txt")
    except Exception as e:
        print(f"[ERROR] 无法读取 ask.txt: {e}")
        return None, None, None
    
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
    
    import time
    start_time = time.time()
    
    try:
        if use_sdk:
            # 使用 OpenAI SDK 方式
            from openai import OpenAI
            
            client = OpenAI(
                api_key=API_KEY,
                base_url=BASE_URL,
            )
            
            # 构建请求参数
            params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": ask_content},
                ],
                "extra_body": {},
            }
            
            completion = client.chat.completions.create(**params)
            result_content = completion.choices[0].message.content
            
            elapsed_time = time.time() - start_time
            print(f"[OK] API 调用成功！耗时: {elapsed_time:.2f}秒")
            
            return result_content, elapsed_time, model
        else:
            # 使用 HTTP API 方式
            import requests
            session = requests.Session()
            if use_proxy:
                session.proxies = proxies
            
            # 手动构建请求
            url = f"{BASE_URL}/chat/completions"
            headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json'
            }
            if TEAM_ID:
                headers['X-Friendli-Team'] = TEAM_ID
                
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
            
            return result_content, elapsed_time, model
            
    except Exception as e:
        print(f"[ERROR] API 调用错误: {e}")
        return None, str(e), model


def main():
    """主函数"""
    print("Friendli.ai API 有效性测试")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"Team ID: {TEAM_ID if TEAM_ID else '未设置'}")
    print(f"Base URL: {BASE_URL}")
    print(f"可用模型: {len(AVAILABLE_MODELS)} 个")
    
    # 显示模型权重分布
    print("\n模型权重分布:")
    distribution = get_weight_distribution()
    for model, info in distribution.items():
        print(f"  {model}: 权重={info['weight']}, 占比={info['percentage']}%")
    print()
    
    # 存储测试结果
    results = []
    
    # 测试1: 使用 SDK 直接访问（自动选择模型）
    print("\n" + "=" * 60)
    print("测试 1: 使用 OpenAI SDK 直接访问（自动选择模型）")
    print("=" * 60)
    result1, time1, model1 = test_chat_completion(use_proxy=False, use_sdk=True)
    results.append(("SDK 直接访问", result1, time1, model1))
    
    # 测试2: 使用 HTTP API 直接访问（自动选择模型）
    print("\n" + "=" * 60)
    print("测试 2: 使用 HTTP API 直接访问（自动选择模型）")
    print("=" * 60)
    result2, time2, model2 = test_chat_completion(use_proxy=False, use_sdk=False)
    results.append(("HTTP API 直接访问", result2, time2, model2))
    
    # 保存结果到 test_result.txt
    print("\n" + "=" * 60)
    print("保存测试结果")
    print("=" * 60)
    
    try:
        with open('test_result.txt', 'w', encoding='utf-8') as f:
            f.write("Friendli.ai API 测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}\n")
            f.write(f"Team ID: {TEAM_ID if TEAM_ID else '未设置'}\n")
            f.write(f"Base URL: {BASE_URL}\n")
            f.write(f"可用模型: {', '.join(AVAILABLE_MODELS)}\n")
            f.write(f"代理: {HTTP_PROXY}\n\n")
            
            # 写入模型权重分布
            f.write("模型权重分布:\n")
            for model, info in distribution.items():
                f.write(f"  {model}: 权重={info['weight']}, 占比={info['percentage']}%\n")
            f.write("\n")
            
            # 从 ask.txt 读取询问内容
            with open('ask.txt', 'r', encoding='utf-8') as af:
                ask_content = af.read()
            
            f.write("询问内容 (来自 ask.txt):\n")
            f.write("-" * 60 + "\n")
            f.write(ask_content)
            f.write("\n" + "-" * 60 + "\n\n")
            
            # 写入测试结果
            for test_name, result, time_info, model_used in results:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"测试方式: {test_name}\n")
                f.write(f"使用模型: {model_used}\n")
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
    
    success_count = sum(1 for _, r, _, _ in results if r is not None)
    total_count = len(results)
    
    for test_name, result, time_info, model_used in results:
        status = "[OK] 成功" if result is not None else "[FAIL] 失败"
        time_str = f"{time_info:.2f}秒" if result is not None else time_info
        print(f"{test_name} (模型: {model_used}): {status} ({time_str})")
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
