#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试文档生成功能
使用 AI 代理生成关于"飞书文件查看优化方案"的文档
"""

import requests
import json

# 主服务地址
API_URL = "http://localhost:5000/v1/chat/completions"

# 测试问题（从 demo_task.txt 读取）
TEST_QUESTION = """
## 背景

用户在和openclaw（ai agent），通过 飞书 的对话过程中，发现查看文件不方便。

用户 要求 openclaw：
对于发文件不方便这个问题，其实还有很多方向可以努力，比如说，我还有一个有公网ip的服务器（代号yun11，操作系统是win2012 上面有 php7.4+mysql5.7+nginx1.15）。 
你如果找不到直接可用的技能或者测试下来效果不如人意，也可以制定一个开发计划，你这边一个py脚本，配合一套简单的php只要让我放到yun11上，你可以将写的文档发给php产生一个链接给我，我点开看html

## 任务

不要再问其他，就按背景信息，高质量完成用户的要求。不用解释直接输出用户要的。
"""

def test_document_generation():
    """测试文档生成功能"""
    
    print("=" * 60)
    print("测试文档生成功能")
    print("=" * 60)
    print()
    
    # 构建请求
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的文档生成助手，能够根据用户需求生成完整、可用的代码和文档。"
            },
            {
                "role": "user",
                "content": TEST_QUESTION
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    print("发送请求到 AI 代理...")
    print(f"API 地址: {API_URL}")
    print(f"使用的模型: {payload['model']}")
    print()
    
    try:
        # 发送请求
        response = requests.post(API_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            # 提取响应内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                print("=" * 60)
                print("AI 生成结果")
                print("=" * 60)
                print()
                print(content)
                print()
                print("=" * 60)
                print("测试完成")
                print("=" * 60)
                
                # 保存结果到文件
                with open('generated_document.md', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("\n结果已保存到: generated_document.md")
                
            else:
                print("错误: 响应格式不正确")
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"错误: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_document_generation()