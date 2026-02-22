from openai import OpenAI

client = OpenAI(
  base_url="https://apis.iflow.cn/v1",
  api_key="<YOUR_IFLOW_API_KEY>",
)

completion = client.chat.completions.create(
  extra_body={},
  model="TBStars2-200B-A13B",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)
