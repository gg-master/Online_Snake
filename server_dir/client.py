import asyncio
import json
import time

import websockets


async def hello():
    uri = "ws://localhost:8080"
    # uri = "ws://my-server-on-websockets.herokuapp.com"
    async with websockets.connect(uri) as websocket:
        print(await websocket.recv())
        await websocket.send(json.dumps({'type': 'create_lobby'}))
        print(await websocket.recv())
        for i in range(10):
            s_t = time.time()
            msg = json.dumps({'type': 'game_data', 'data': f"{i} msg"})
            await websocket.send(msg)

            data = json.loads(await websocket.recv())
            e_t = time.time()
            print(data, ' // ', e_t - s_t)


asyncio.get_event_loop().run_until_complete(hello())
