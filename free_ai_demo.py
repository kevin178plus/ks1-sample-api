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

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
  },
  data=json.dumps({
    "model": "openrouter/free",
    "messages": [
      {
        "role": "user",
        "content": "Hello! What can you help me with today?"
      }
    ]
  })
)

data = response.json()
print(data['choices'][0]['message']['content'])
# Check which model was selected
print('Model used:', data['model'])
