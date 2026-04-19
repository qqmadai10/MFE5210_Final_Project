import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class Event:
    type: str
    data: Any

class EventBus:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False

    async def start(self):
        self._running = True
        await self._dispatch()

    async def stop(self):
        self._running = False

    async def put(self, event: Event):
        await self._queue.put(event)

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    async def _dispatch(self):
        while self._running:
            event = await self._queue.get()
            for handler in self._handlers.get(event.type, []):
                await handler(event)