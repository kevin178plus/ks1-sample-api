#!/usr/bin/env python3
"""
测试 Google Gemini API 连接
"""
import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(os.path.dirname(script_dir))
load_dotenv(os.path.join(project_dir, '.env'))

def test_gemini_api():
    """测试Gemini API是否可用"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("[ERROR] 未找到 GEMINI_API_KEY")
        print("请在 .env 文件中设置 GEMINI_API_KEY")
        return False
    
    print(f"[OK] 找到 API Key (前缀: {api_key[:20]}...)")
    
    try:
        from google import genai
        
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents="Hello!"
        )
        
        print("[OK] API 连接成功!")
        print(f"   模型: gemini-3-flash-preview")
        print(f"   内容: {response.text}")
        return True
        
    except ImportError:
        print("[ERROR] 未安装 google-genai SDK")
        print("请运行: pip install google-genai")
        return False
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False

def list_models():
    """列出可用模型"""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("[ERROR] 未找到 GEMINI_API_KEY")
        return
    
    try:
        from google import genai
        
        client = genai.Client(api_key=api_key)
        
        print("\nAvailable Models:")
        print("-" * 60)
        
        # 列出所有模型
        models = client.models.list()
        for model in models:
            model_id = model.name.replace('models/', '')
            print(f"  * {model_id}")
            
    except ImportError:
        print("[ERROR] 未安装 google-genai SDK")
    except Exception as e:
        print(f"[FAIL] 获取模型列表失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Google Gemini API Test")
    print("=" * 60)
    
    success = test_gemini_api()
    
    # 不显示模型列表，避免长时间等待
    # if success:
    #     print("\n" + "=" * 60)
    #     list_models()
    
    sys.exit(0 if success else 1)
