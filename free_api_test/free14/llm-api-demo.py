# -*- coding: utf-8 -*-
import sys
import io

# 修复 Windows 终端中文输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx
import ssl
import truststore
import json

# 原 API 配置
API_URL = "https://cgc.chancloud.com/cgc/api/public/ai/server/chat/stream"
API_KEY = "cgc-apikey-Q8gx3J_XSs4C7b12KCE09N7wrZBaAE5PIW0eJAMEDhaa2UF7"
MODEL = "Nemotron-3-Super-120B-A12B"

print(f"API URL: {API_URL}")
print(f"Model: {MODEL}")

# 使用 truststore 处理 SSL 证书
ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

http_client = httpx.Client(
    verify=ctx,
    timeout=120.0
)

print("\n正在调用 LLM API...\n")

# 请求
response = http_client.post(
    API_URL,
    json={
        "model": MODEL,
        "messages": [{"role": "user", "content": "写一首关于GPU计算性能的打油诗"}],
        "temperature": 0.5,
        "top_p": 1,
        "max_tokens": 1024,
        "stream": True
    },
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    # 解析 SSE 流
    full_content = ""
    lines = response.text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('data:'):
            # 处理 "data:xxx" 或 "data: xxx" 格式
            data = line[5:].strip()  # 移除 'data:' 前缀
            if data == '[DONE]':
                break
            # 检查是否是错误消息
            if 'Error:' in data or 'event:error' in line:
                print(f"Event: {data[:100]}")
                continue
            try:
                chunk_obj = json.loads(data)
                if 'choices' in chunk_obj and len(chunk_obj['choices']) > 0:
                    delta = chunk_obj['choices'][0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        full_content += content
                        print(f"Chunk: {content[:30]}...")
            except json.JSONDecodeError as e:
                print(f"Parse error: {e}, data: {data[:100]}")
    
    print("\n=== LLM 响应 ===")
    print(full_content)
else:
    print(f"Error: {response.text}")
