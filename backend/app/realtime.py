import asyncio
from collections import deque
from fastapi import WebSocket

class EventHub:
    def __init__(self):
        self.history = deque(maxlen=100)
        self.clients: set[asyncio.Queue] = set()

    def publish(self, event: dict):
        self.history.append(event)
        for queue in list(self.clients):
            queue.put_nowait(event)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        await websocket.send_json({'type': 'CONNECTED', 'history_size': len(self.history)})
        queue = asyncio.Queue()
        self.clients.add(queue)
        try:
            for event in self.history:
                await websocket.send_json(event)
            while True:
                event = await queue.get()
                await websocket.send_json(event)
        except Exception:
            self.clients.discard(queue)

hub = EventHub()
