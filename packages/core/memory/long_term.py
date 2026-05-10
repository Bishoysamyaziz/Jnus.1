"""OneAgent OS — Long Term Memory (PostgreSQL)
Persistent storage for conversation history and user profiles.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional


class LongTermMemory:
    """PostgreSQL — history كامل + user profiles"""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "POSTGRES_URL",
            "postgresql://user:pass@localhost:5432/oneagent",
        )
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            import asyncpg
            self._pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        return self._pool

    async def ensure_tables(self):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    conversation_id UUID REFERENCES conversations(id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tokens INT DEFAULT 0,
                    cost DECIMAL(10,6) DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    preferences JSONB DEFAULT '{}',
                    personality JSONB DEFAULT '{}',
                    goals JSONB DEFAULT '[]',
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS task_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    task TEXT NOT NULL,
                    result TEXT,
                    duration_ms FLOAT DEFAULT 0,
                    cost DECIMAL(10,6) DEFAULT 0,
                    success BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

    async def save_conversation(self, user_id: str, session_id: str) -> str:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO conversations (user_id, session_id) VALUES ($1, $2) RETURNING id",
                user_id, session_id,
            )
            return str(row["id"])

    async def save_message(self, conversation_id: str, role: str, content: str, tokens: int = 0, cost: float = 0):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO messages (conversation_id, role, content, tokens, cost) VALUES ($1, $2, $3, $4, $5)",
                conversation_id, role, content, tokens, cost,
            )

    async def get_history(self, user_id: str, limit: int = 50) -> list[dict]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT m.role, m.content, m.tokens, m.cost, m.created_at
                   FROM messages m
                   JOIN conversations c ON m.conversation_id = c.id
                   WHERE c.user_id = $1
                   ORDER BY m.created_at DESC
                   LIMIT $2""",
                user_id, limit,
            )
            return [dict(r) for r in rows]

    async def health(self) -> bool:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
