
from openai import OpenAI
import httpx
import truststore

ctx = truststore.SSLContext()

http_client = httpx.Client(
    verify=ctx,
    timeout=60.0
)

client = OpenAI(
    base_url="https://cgc.chancloud.com/cgc/api/public/ai/server",
    api_key="cgc-apikey-Q8gx3J_XSs4C7b12KCE09N7wrZBaAE5PIW0eJAMEDhaa2UF7",
    http_client=http_client
)

completion = client.chat.completions.create(
    model="Nemotron-3-Super-120B-A12B",
    messages=[
        {"role": "user", "content": "写一首关于GPU计算性能的打油诗"}
    ]
)

print(completion.choices[0].message.content)
