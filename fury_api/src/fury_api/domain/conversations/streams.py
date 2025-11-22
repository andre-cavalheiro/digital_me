from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator
from typing import Any


class AssistantStreamBroker:
    def __init__(self) -> None:
        self._queues: dict[int, set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def stream(self, conversation_id: int) -> AsyncGenerator[dict[str, Any], None]:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._queues[conversation_id].add(queue)

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                queues = self._queues.get(conversation_id)
                if queues is not None:
                    queues.discard(queue)
                    if not queues:
                        self._queues.pop(conversation_id, None)

    async def publish(self, conversation_id: int, event: dict[str, Any]) -> None:
        async with self._lock:
            queues = list(self._queues.get(conversation_id, []))

        for queue in queues:
            await queue.put(event)


assistant_stream_broker = AssistantStreamBroker()

_STUB_STAGES = (
    ("status", {"stage": "queued"}),
    ("status", {"stage": "generating"}),
    ("completed", {"stage": "completed"}),
)


async def emit_mock_progress(conversation_id: int, assistant_message_id: int) -> None:
    for event_type, payload in _STUB_STAGES:
        await assistant_stream_broker.publish(
            conversation_id,
            {
                "type": event_type,
                "conversation_id": conversation_id,
                "assistant_message_id": assistant_message_id,
                **payload,
            },
        )
        await asyncio.sleep(0.5)


def schedule_mock_progress(conversation_id: int, assistant_message_id: int) -> None:
    asyncio.create_task(emit_mock_progress(conversation_id, assistant_message_id))
