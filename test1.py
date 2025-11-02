import os
import asyncio
from dotenv import load_dotenv

from okx.websocket.WsPrivateAsync import WsPrivateAsync
load_dotenv()

def callbackFunc(message):
    print(message)

async def main():

    ws = WsPrivateAsync(
        apiKey = os.getenv('OKX_API_KEY'),
        passphrase = os.getenv('OKX_PASSWORD'),
        secretKey = os.getenv('OKX_SECRET'),
        url = "wss://ws.okx.com:8443/ws/v5/private",
        useServerTime=False
    )
    await ws.start()
    args = [{
        "channel": "balance_and_position"
    }]

    await ws.subscribe(args, callback=callbackFunc)
    await asyncio.sleep(10)

    await ws.unsubscribe(args, callback=callbackFunc)
    await asyncio.sleep(10)


asyncio.run(main())