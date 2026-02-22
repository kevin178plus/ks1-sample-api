import requests

# 配置 API
url = "https://apis.iflow.cn/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

# 请求数据
data = {
    "model": "TBStars2-200B-A13B", 
    "messages": [
        {"role": "user", "content": "解释一下量子计算的基本原理"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
}

# 发起请求
response = requests.post(url, json=data, headers=headers)
result = response.json()

# 打印结果
print(result["choices"][0]["message"]["content"])
