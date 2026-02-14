import requests
import json

response = requests.get(
  url="https://openrouter.ai/api/v1/key",
  headers={
    "Authorization": f"Bearer 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"
  }
)

print(json.dumps(response.json(), indent=2))
