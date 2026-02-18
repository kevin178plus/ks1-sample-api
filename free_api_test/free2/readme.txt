# chatanywhere.

## 免费版	
	支持	gpt-5.2, gpt-5.1, gpt-5, gpt-4o，gpt-4.1 一天5次；
	支持	deepseek-r1, deepseek-v3, deepseek-v3-2-exp	一天30次，
	支持	gpt-4o-mini，gpt-3.5-turbo，gpt-4.1-mini，gpt-4.1-nano, gpt-5-mini，gpt-5-nano	一天200次。

## 一天总共可用200次

## key
您的免费API Key为: sk-RJeQTUufTH2oUcdLLyOIMZbxFQNwVZdi622xyZaCEJV7ltLt

## 转发Host1
	https://api.chatanywhere.tech	(国内中转，延时更低)

## demo 列出模型

```
import requests

url = "https://api.chatanywhere.tech/v1/models"

payload={}
headers = {
   'Authorization': 'Bearer sk-xxxxxxxxxx'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
```

## demo chat

```
import requests
import json

url = "https://api.chatanywhere.tech/v1/chat/completions"

payload = json.dumps({
   "model": "gpt-3.5-turbo",
   "messages": [
      {
         "role": "system",
         "content": "You are a helpful assistant."
      },
      {
         "role": "user",
         "content": "Hello!"
      }
   ]
})
headers = {
   'Authorization': 'Bearer sk-xxxxxxxxxx',
   'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```