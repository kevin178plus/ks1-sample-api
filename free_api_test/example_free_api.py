import requests
import json
import os

# 从 .env 文件读取 API Key
def load_env():
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")

# Free API endpoint
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Request headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "Free API Test",
    "Content-Type": "application/json"
}

# Request payload
payload = {
    "model": "openrouter/free",
    "messages": [
        {
            "role": "user",
            "content": "Hello! Can you help me with a simple task?"
        }
    ]
}

# Make the API request
response = requests.post(API_URL, headers=headers, json=payload)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    print("Response:")
    print(data['choices'][0]['message']['content'])
    print(f"Model used: {data.get('model', 'N/A')}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
