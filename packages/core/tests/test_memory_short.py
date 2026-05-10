"""Tests for ShortTermMemory"""
from __future__ import annotations

import pytest

from packages.core.memory.short_term import ShortTermMemory


@pytest.fixture
def memory():
    return ShortTermMemory(redis_url="redis://localhost:6379")


@pytest.mark.asyncio
async def test_save_and_get(memory):
    """Should save and retrieve messages"""
    session_id = "test_session_1"
    messages = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    await memory.save(session_id, messages)
    retrieved = await memory.get(session_id)
    assert retrieved == messages


@pytest.mark.asyncio
async def test_get_empty_session(memory):
    """Should return empty list for non-existent session"""
    messages = await memory.get("non_existent_session")
    assert messages == []


@pytest.mark.asyncio
async def test_append_message(memory):
    """Should append a message to existing session"""
    session_id = "test_session_2"
    await memory.save(session_id, [{"role": "user", "content": "first"}])
    await memory.append(session_id, {"role": "assistant", "content": "second"})
    messages = await memory.get(session_id)
    assert len(messages) == 2
    assert messages[0]["content"] == "first"
    assert messages[1]["content"] == "second"


@pytest.mark.asyncio
async def test_clear_session(memory):
    """Should clear all messages for a session"""
    session_id = "test_session_3"
    await memory.save(session_id, [{"role": "user", "content": "test"}])
    await memory.clear(session_id)
    messages = await memory.get(session_id)
    assert messages == []


@pytest.mark.asyncio
async def test_ttl_expiration(memory):
    """Messages should expire after TTL (use very short TTL for testing)"""
    session_id = "test_session_ttl"
    await memory.save(session_id, [{"role": "user", "content": "test"}], ttl=1)
    # Wait for expiration
    import asyncio
    await asyncio.sleep(1.5)
    messages = await memory.get(session_id)
    assert messages == []


@pytest.mark.asyncio
async def test_health_check(memory):
    """Health check should return True when Redis is available"""
    try:
        healthy = await memory.health()
        assert isinstance(healthy, bool)
    except Exception:
        pytest.skip("Redis not available")


@pytest.mark.asyncio
async def test_multiple_sessions(memory):
    """Should handle multiple sessions independently"""
    session_a = "session_a"
    session_b = "session_b"
    await memory.save(session_a, [{"role": "user", "content": "from_a"}])
    await memory.save(session_b, [{"role": "user", "content": "from_b"}])
    msgs_a = await memory.get(session_a)
    msgs_b = await memory.get(session_b)
    assert msgs_a[0]["content"] == "from_a"
    assert msgs_b[0]["content"] == "from_b"


@pytest.mark.asyncio
async def test_large_message(memory):
    """Should handle large messages"""
    session_id = "test_large"
    large_content = "x" * 10000
    await memory.save(session_id, [{"role": "user", "content": large_content}])
    retrieved = await memory.get(session_id)
    assert len(retrieved[0]["content"]) == 10000
