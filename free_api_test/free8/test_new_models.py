#!/usr/bin/env python3
"""
测试 free8 新增的模型
测试: meta-llama/Llama-3.3-70B-Instruct 和 Qwen/Qwen3-235B-A22B-Instruct-2507
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入配置
from config import (
    API_KEY, TEAM_ID, BASE_URL,
    USE_PROXY, HTTP_PROXY, USE_SDK,
)

if not API_KEY:
    raise ValueError("FRIENDLI_TOKEN not found in .env file")

# 要测试的模型列表
TEST_MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct",
    "Qwen/Qwen3-235B-A22B-Instruct-2507",
]


def test_chat_completion(model):
    """测试指定模型的聊天完成 API"""
    print("=" * 50)
    print(f"测试模型: {model}")
    print("=" * 50)
    
    # 从 ask.txt 读取询问内容
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            ask_content = f.read()
        print(f"[OK] 成功读取 ask.txt (内容长度: {len(ask_content)} 字符)")
    except Exception as e:
        print(f"[ERROR] 无法读取 ask.txt: {e}")
        return None, None
    
    import time
    start_time = time.time()
    
    try:
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
        }
        
        completion = client.chat.completions.create(**params)
        result_content = completion.choices[0].message.content
        
        elapsed_time = time.time() - start_time
        print(f"[OK] API 调用成功！耗时: {elapsed_time:.2f}秒")
        
        return result_content, elapsed_time
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[ERROR] API 调用错误: {e}")
        return None, str(e)


def main():
    """主函数"""
    print("=" * 60)
    print("Friendli.ai 新增模型测试")
    print("=" * 60)
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"Team ID: {TEAM_ID if TEAM_ID else '未设置'}")
    print(f"Base URL: {BASE_URL}")
    print()
    
    # 存储测试结果
    results = []
    
    # 依次测试每个模型
    for model in TEST_MODELS:
        print(f"\n{'=' * 60}")
        print(f"测试模型: {model}")
        print("=" * 60)
        
        result, time_info = test_chat_completion(model)
        results.append((model, result, time_info))
        
        # 每个模型测试之间加个间隔
        print("\n" + "-" * 40)
    
    # 保存结果
    print("\n" + "=" * 60)
    print("保存测试结果")
    print("=" * 60)
    
    try:
        with open('test_new_models_result.txt', 'w', encoding='utf-8') as f:
            f.write("Friendli.ai 新增模型测试结果\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}\n")
            f.write(f"Team ID: {TEAM_ID if TEAM_ID else '未设置'}\n")
            f.write(f"Base URL: {BASE_URL}\n\n")
            
            # 从 ask.txt 读取询问内容
            with open('ask.txt', 'r', encoding='utf-8') as af:
                ask_content = af.read()
            
            f.write("询问内容 (来自 ask.txt):\n")
            f.write("-" * 60 + "\n")
            f.write(ask_content)
            f.write("\n" + "-" * 60 + "\n\n")
            
            # 写入测试结果
            for model, result, time_info in results:
                f.write(f"\n{'=' * 60}\n")
                f.write(f"模型: {model}")
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
        
        print("[OK] 结果已保存到 test_new_models_result.txt")
    except Exception as e:
        print(f"[ERROR] 保存结果失败: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    success_count = sum(1 for _, r, _ in results if r is not None)
    total_count = len(results)
    
    for model, result, time_info in results:
        status = "[OK] 成功" if result is not None else "[FAIL] 失败"
        time_str = f"{time_info:.2f}秒" if result is not None else time_info
        print(f"{model}: {status} ({time_str})")
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
