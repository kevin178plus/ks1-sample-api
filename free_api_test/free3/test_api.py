#!/usr/bin/env python3
"""
API 有效性测试脚本
测试 free_chatgpt_api 是否能正常工作
根据 README.md 示例改造
"""

import openai
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API 配置（来自 README）
api_key = os.getenv("FREE3_API_KEY")
if not api_key:
    raise ValueError("FREE3_API_KEY not found in .env file")
openai.api_key = api_key
openai.base_url = "https://free.v36.cm/v1/"

def test_chat_completion(model="gpt-4o-mini"):
    """测试聊天完成 API"""
    print("=" * 50)
    print(f"测试 API: 聊天完成 (模型: {model})")
    print("=" * 50)
    
    # 从 ask.txt 读取询问内容
    try:
        with open('ask.txt', 'r', encoding='utf-8') as f:
            ask_content = f.read()
        print("[OK] 成功读取 ask.txt")
    except Exception as e:
        print(f"[ERROR] 无法读取 ask.txt: {e}")
        return False
    
    try:
        # 调用 API（参考 README 示例）
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": ask_content,
                },
            ],
        )
        
        # 获取回复内容
        result_content = completion.choices[0].message.content
        
        print(f"[OK] API 调用成功！")
        
        # 保存结果到 test_result.txt
        with open('test_result.txt', 'w', encoding='utf-8') as f:
            f.write("API 测试结果\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"模型: {model}\n")
            f.write(f"API: {openai.base_url}\n\n")
            f.write("询问内容 (来自 ask.txt):\n")
            f.write("-" * 50 + "\n")
            f.write(ask_content)
            f.write("\n" + "-" * 50 + "\n\n")
            f.write("AI 回复:\n")
            f.write("-" * 50 + "\n")
            f.write(result_content)
            f.write("\n" + "-" * 50 + "\n")
        
        print(f"[OK] 结果已保存到 test_result.txt")
        print(f"\nAI 回复预览:\n{result_content[:200]}...")
        return True
        
    except Exception as e:
        print(f"[ERROR] API 调用错误: {e}")
        return False

def main():
    """主函数"""
    print("Free ChatGPT API 有效性测试")
    print(f"API Key: {openai.api_key[:10]}...{openai.api_key[-4:]}")
    print(f"Base URL: {openai.base_url}\n")
    
    # 测试 API
    result = test_chat_completion("gpt-4o-mini")
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    if result:
        print("[PASS] API 测试通过！")
        return 0
    else:
        print("[FAIL] API 测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
