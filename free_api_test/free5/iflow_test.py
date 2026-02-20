from iflow_sdk import query
import asyncio

async def main():
    response = await query("法国的首都是哪里？")
    print(response)  # 输出：法国的首都是巴黎。

asyncio.run(main())
