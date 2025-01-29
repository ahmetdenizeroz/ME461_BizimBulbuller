import asyncio
import websockets

async def connect():
    async with websockets.connect("ws://192.168.4.1:8080") as ws:  # Pico W's AP IP
        await ws.send("PING")
        response = await ws.recv()
        print("Response:", response)

asyncio.run(connect())

