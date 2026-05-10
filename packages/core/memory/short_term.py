"""OneAgent OS — Short Term Memory (Redis)
Context window for the current session with TTL.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional


class ShortTermMemory:
    """Redis TTL=1h — context window الحالي"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def save(self, session_id: str, messages: list[dict], ttl: int = 3600):
        r = await self._get_redis()
        key = f"session:{session_id}:messages"
        await r.setex(key, ttl, json.dumps(messages))

    async def get(self, session_id: str) -> list[dict]:
        r = await self._get_redis()
        data = await r.get(f"session:{session_id}:messages")
        return json.loads(data) if data else []

    async def append(self, session_id: str, message: dict, ttl: int = 3600):
        messages = await self.get(session_id)
        messages.append(message)
        await self.save(session_id, messages, ttl)

    async def clear(self, session_id: str):
        r = await self._get_redis()
        await r.delete(f"session:{session_id}:messages")

    async def health(self) -> bool:
        try:
            r = await self._get_redis()
            await r.ping()
            return True
        except Exception:
            return False
