
import requests, base64

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False


headers = {
  "Authorization": "Bearer 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",
  "Accept": "text/event-stream" if stream else "application/json"
}

payload = {
  "model": "z-ai/glm4.7",
  "messages": [{"role":"user","content":"How many 'r's are in the word 'strawberry'?"}],
  "max_tokens": 1024,
  "temperature": 0.20,
  "top_p": 1.00,
  "stream": stream,
  "chat_template_kwargs": {"thinking":True},
}



response = requests.post(invoke_url, headers=headers, json=payload)

if stream:
    for line in response.iter_lines():
        if line:
            print(line.decode("utf-8"))
else:
    print(response.json())
