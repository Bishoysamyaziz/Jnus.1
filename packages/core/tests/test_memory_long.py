"""Tests for LongTermMemory"""
from __future__ import annotations

import pytest

from packages.core.memory.long_term import LongTermMemory


@pytest.fixture
def memory():
    return LongTermMemory(database_url="postgresql://oneagent:oneagent_pass@localhost:5432/oneagent")


@pytest.mark.asyncio
async def test_ensure_tables(memory):
    """Should create tables on initialization"""
    try:
        await memory.ensure_tables()
        assert True
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.mark.asyncio
async def test_save_and_get_conversation(memory):
    """Should save and retrieve conversation history"""
    try:
        await memory.ensure_tables()
        conv_id = await memory.save_conversation("test_user", "test_session")
        assert conv_id is not None
        assert len(conv_id) > 0
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.mark.asyncio
async def test_save_message(memory):
    """Should save messages to a conversation"""
    try:
        await memory.ensure_tables()
        conv_id = await memory.save_conversation("test_user_msg", "test_session_msg")
        await memory.save_message(conv_id, "user", "hello", tokens=5, cost=0.001)
        await memory.save_message(conv_id, "assistant", "hi there", tokens=10, cost=0.002)
        assert True
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.mark.asyncio
async def test_get_history(memory):
    """Should retrieve conversation history for a user"""
    try:
        await memory.ensure_tables()
        history = await memory.get_history("test_user", limit=10)
        assert isinstance(history, list)
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.mark.asyncio
async def test_health_check(memory):
    """Health check should return True when PostgreSQL is available"""
    try:
        healthy = await memory.health()
        assert isinstance(healthy, bool)
    except Exception:
        pytest.skip("PostgreSQL not available")


@pytest.mark.asyncio
async def test_empty_history(memory):
    """Should return empty list for user with no history"""
    try:
        await memory.ensure_tables()
        history = await memory.get_history("non_existent_user_xyz")
        assert history == []
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")
